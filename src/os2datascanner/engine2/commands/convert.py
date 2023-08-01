import json
import click
import traceback

from ..model.core import SourceManager
from ..model.file import FilesystemHandle

from ..conversions.types import OutputType
from ..conversions.utilities.cache import CacheManager


def try_convert(sm, handle, output_type, mime_override: str = None):
    resource = handle.follow(sm)
    cm = CacheManager(resource)
    try:
        form = cm.representation(output_type)
        if form.cache_exists:
            yield (handle, form.get(), True)
        else:
            yield (handle, form.create(mime_override=mime_override), False)
    except KeyError:
        manifest = cm.representation(OutputType.Manifest)
        try:
            files = manifest.get(create=True)
            if files:
                for h in files:
                    yield from try_convert(sm, h, output_type)
            else:
                yield (handle, None, False)
        except KeyError:
            yield (handle, None, False)
    except Exception:
        traceback.print_exc()
        yield (handle, None, False)


@click.command(
        help="Generate an engine2 representation of a file.")
@click.option(
        "-t", "--type", "type_id",
        type=click.Choice([ot.value for ot in OutputType]),
        help="the conversion to perform",
        default="text", show_default=True)
@click.option(
        "-r", "--raw",
        is_flag=True,
        help="just print the representation with no headers or indentation",
        default=False, show_default=True)
@click.argument(
        "files_to_convert", nargs=-1, required=True)
def main(type_id, raw, files_to_convert) -> int:  # noqa:CCR001
    output_type = OutputType(type_id)
    sm = SourceManager()

    for f in files_to_convert:
        mime = None
        if "::" in f:
            f, mime = f.split("::", maxsplit=1)
        fh = FilesystemHandle.make_handle(f)

        for handle, form, cache in try_convert(sm, fh, output_type, mime):
            encoded_form = (
                    json.dumps(
                            output_type.encode_json_object(form),
                            indent=4 if not raw else None)
                    if form else "no conversion possible")
            if not raw:
                print(f"{handle}{' (from cache)' if cache else ''}")
                print("\n".join(
                        f"    {line}" for line in encoded_form.split("\n")))
            else:
                print(encoded_form, end="")


if __name__ == "__main__":
    main()
