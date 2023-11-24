import json
import structlog

from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F

from ..models.rules.customrule import CustomRule

from os2datascanner.engine2.rules.rule import Rule
from os2datascanner.engine2.model.core import SourceManager
from os2datascanner.engine2.model.file import FilesystemHandle
from os2datascanner.engine2.model.utilities.temp_resource import (
        NamedTemporaryResource)
from os2datascanner.engine2.pipeline import messages, worker
from os2datascanner.projects.admin import settings
from os2datascanner.engine2.utilities.timeout import run_with_default_timeout


logger = structlog.get_logger(__name__)


class MiniScanner(TemplateView, LoginRequiredMixin):
    template_name = "miniscan.html"

    def dispatch(self, request, *args, **kwargs):
        if (settings.MINISCAN_REQUIRES_LOGIN
                and not request.user.is_authenticated):
            return self.handle_no_permission()
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_context_data(self):
        context = super().get_context_data()
        context["customrule_list"] = CustomRule.objects.annotate(rule_field=F("_rule"))

        return context


def execute_mini_scan(request):  # noqa:CCR001
    context = {
        "file_obj": (file_obj := request.FILES.get("file")),
        "raw_rule": (raw_rule := request.POST.get("rule")),
        "halfbaked_rule": (halfbaked_rule := json.loads(raw_rule or "null")),

        "replies": (replies := []),
    }

    rule = None
    if halfbaked_rule:
        rule = Rule.from_json_object(halfbaked_rule)

    if file_obj and rule:
        with NamedTemporaryResource(file_obj.name) as ntr:

            with ntr.open("wb") as fp:
                fp.write(file_obj.read())

            if ntr.size() <= settings.MINISCAN_FILE_SIZE_LIMIT:

                def _run_mini_pipeline():
                    handle = FilesystemHandle.make_handle(ntr.get_path())

                    conv = messages.ConversionMessage(
                        scan_spec=messages.ScanSpecMessage(
                            scan_tag=messages.ScanTagFragment.make_dummy(),
                            source=handle.source,
                            rule=rule,
                            filter_rule=None,
                            configuration={},
                            progress=None),
                        handle=handle,
                        progress=messages.ProgressFragment(
                            rule=rule,
                            matches=[]),
                        ).to_json_object()

                    for channel, message_ in worker.process(SourceManager(), conv):
                        if channel in ("os2ds_matches",):
                            message = messages.MatchesMessage.from_json_object(
                                message_)

                            if not message.matched:
                                continue

                            replies.append(message)

                finished, _ = run_with_default_timeout(_run_mini_pipeline)

                if not finished:
                    logger.warning("Miniscanner - Timeout encountered: scan took too long.")
            else:
                logger.warning("Miniscanner - Rejected file that exceeded the size limit.")

    return render(request, "components/miniscanner/miniscan_results.html", context)
