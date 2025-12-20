import json
import os
import tempfile

from django.apps import apps
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.generic import View
from libs.utils.tempfile import can_delete, write_doc
from root.pdf_generator import PdfGenerator
from root.settings import BASE_DIR
from root.utils import render_to_pdf
from weasyprint import CSS, HTML


def generate_pdf(
    request,
    app,
    model_name,
    id,
    header=None,
    main=None,
    filename=None,
    extra_data={},
    no_margin=False,
):
    model = apps.get_model(app, model_name)
    try:
        data = model.objects.get(id=id)
    except:
        return HttpResponse("objet n'existe plus")
    if header:
        header = render_to_string(header, {"data": data, "extra_data": extra_data})
    if main is None:
        main = f"{app}/{model_name.lower()}.html"
    main = render_to_string(
        main,
        {"data": data, "extra_data": extra_data},
    )

    annexes = []

    generator = PdfGenerator(
        main_html=main,
        header_html=header if header else None,
        base_url=os.path.join(BASE_DIR, "build"),
    )

    result = generator.render_pdf(
        annexes,
    )
    response = HttpResponse(content_type="application/pdf;")
    if filename is None:
        filename = model_name
    content = f"inline; filename={filename}.pdf"
    download = request.GET.get("download")
    if download:
        content = f"attachment; filename='{filename}.pdf'"
    response["Content-Disposition"] = content
    response["Content-Transfer-Encoding"] = "binary"

    # with tempfile.NamedTemporaryFile(delete=True) as output:
    #     output.write(result)
    #     output.flush()
    #     output = open(output.name, 'br')
    #     response.write(output.read())
    return write_doc(result, response)


def generate_pdf_custom(
    request, app, model_name, data, header=None, main=None, filename=None, extra_data={}
):
    if header:
        header = render_to_string(header, data)
    if main is None:
        main = f"{app}/{model_name.lower()}.html"
    main = render_to_string(
        main,
        data,
    )

    annexes = []

    generator = PdfGenerator(
        main_html=main,
        header_html=header if header else None,
        base_url=os.path.join(BASE_DIR, "build"),
    )

    result = generator.render_pdf(
        annexes,
    )
    response = HttpResponse(content_type="application/pdf;")
    if filename is None:
        filename = model_name
    content = f"inline; filename={filename}.pdf"
    download = request.GET.get("download")
    if download:
        content = f"attachment; filename='{filename}.pdf'"
    response["Content-Disposition"] = content
    response["Content-Transfer-Encoding"] = "binary"

    with tempfile.NamedTemporaryFile(delete=can_delete) as output:
        output.write(result)
        output.flush()
        output = open(output.name, "br")
        response.write(output.read())
    return response


from libs.utils.get_user import get_current_request


def generate_pdf_custom_file(
    app, model_name, data, header=None, main=None, filename=None, extra_data={}
):
    """
    Generates a PDF file and returns the open file object.
    """
    if header:
        header = render_to_string(header, data)
    if main is None:
        main = f"{app}/{model_name.lower()}.html"
    main = render_to_string(main, data)

    annexes = []

    generator = PdfGenerator(
        main_html=main,
        header_html=header if header else None,
        base_url=os.path.join(BASE_DIR, "build"),
    )

    result = generator.render_pdf(annexes)

    if filename is None:
        filename = model_name

    # Create a temporary file and keep it open
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w+b", suffix=".pdf")
    temp_file.write(result)
    temp_file.flush()  # Ensure all data is written
    temp_file.seek(0)  # Reset the file pointer to the beginning for reading

    return temp_file


# def generate_pdf_custom_file(
#     app, model_name, data, header=None, main=None, filename=None, extra_data={}
# ):
#     """
#     Generates a PDF file and returns the path to the temporary file.
#     """
#     if header:
#         header = render_to_string(header, data)
#     if main is None:
#         main = f"{app}/{model_name.lower()}.html"
#     main = render_to_string(main, data)

#     annexes = []

#     generator = PdfGenerator(
#         main_html=main,
#         header_html=header if header else None,
#         base_url=os.path.join(BASE_DIR, "build"),
#     )

#     result = generator.render_pdf(annexes)

#     if filename is None:
#         filename = model_name

#     # Create a named temporary file
#     temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
#     try:
#         temp_file.write(result)
#         temp_file.flush()  # Ensure all data is written
#         temp_file_path = temp_file.name  # Get the file path
#     finally:
#         temp_file.close()  # Close the file to release any locks

#     return temp_file_path


from libs.utils.tempfile import can_delete


def generate_pdf_with_data(
    request,
    main,
    main_data,
    header=None,
    header_data=None,
    filename=None,
):
    header = render_to_string(header, header_data)
    main = render_to_string(main, main_data)
    annexes = []
    generator = PdfGenerator(
        main_html=main,
        header_html=header,
        base_url=os.path.join(BASE_DIR, "build"),
    )
    result = generator.render_pdf(
        annexes,
    )
    response = HttpResponse(content_type="application/pdf;")
    content = f"inline; filename={filename}.pdf"
    download = request.GET.get("download")
    if download:
        content = f"attachment; filename='{filename}.pdf'"
    response["Content-Disposition"] = content
    response["Content-Transfer-Encoding"] = "binary"

    with tempfile.NamedTemporaryFile(delete=can_delete) as output:
        output.write(result)
        output.flush()
        output = open(output.name, "br")
        response.write(output.read())
    return response
