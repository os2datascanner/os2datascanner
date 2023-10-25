from django.db import models
from django.utils.translation import gettext_lazy as _

from .account import Account


class AccountOutlookSetting(models.Model):
    class OutlookCategoryColour(models.TextChoices):
        # Available colour presets are defined here:
        # https://learn.microsoft.com/en-us/graph/api/resources/outlookcategory?view=graph-rest-1.0#properties
        Red = "Preset0", _("Red")
        Orange = "Preset1", _("Orange")
        Brown = "Preset2", _("Brown")
        Yellow = "Preset3", _("Yellow")
        Green = "Preset4", _("Green")
        Teal = "Preset5", _("Teal")
        Olive = "Preset6", _("Olive")
        Blue = "Preset7", _("Blue")
        Purple = "Preset8", _("Purple")
        Cranberry = "Preset9", _("Cranberry")
        Steel = "Preset10", _("Steel")
        DarkSteel = "Preset11", _("Dark Steel")
        Gray = "Preset12", _("Gray")
        DarkGray = "Preset13", _("Dark Gray")
        Black = "Preset14", _("Black")
        DarkRed = "Preset15", _("Dark Red")
        DarkOrange = "Preset16", _("Dark Orange")
        DarkBrown = "Preset17", _("Dark Brown")
        DarkYellow = "Preset18", _("Dark Yellow")
        DarkGreen = "Preset19", _("Dark Green")
        DarkTeal = "Preset20", _("Dark Teal")
        DarkOlive = "Preset21", _("Dark Olive")
        DarkBlue = "Preset22", _("Dark Blue")
        DarkPurple = "Preset23", _("Dark Purple")
        DarkCranberry = "Preset24", _("Dark Cranberry")

    account = models.OneToOneField(Account,
                                   null=True,
                                   on_delete=models.SET_NULL,
                                   related_name="outlook_settings")

    account_username = models.CharField(max_length=256)

    categorize_email = models.BooleanField(default=False,
                                           verbose_name=_("Categorize emails"))

    # UUID from MSGraph category creation
    # We'll only ever need it in str format, so no need for UUID field.
    match_category_uuid = models.CharField(max_length=36,
                                           null=True,
                                           blank=True,
                                           )

    match_colour = models.CharField(max_length=10,
                                    choices=OutlookCategoryColour.choices,
                                    verbose_name=_("Category colour for matches"),
                                    default=OutlookCategoryColour.DarkRed,
                                    )

    false_positive_category_uuid = models.CharField(max_length=36,
                                                    null=True,
                                                    blank=True,
                                                    )

    false_positive_colour = models.CharField(max_length=10,
                                             choices=OutlookCategoryColour.choices,
                                             verbose_name=_("Category colour for false positives"),
                                             default=OutlookCategoryColour.DarkGreen)
