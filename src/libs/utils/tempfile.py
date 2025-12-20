import platform
import tempfile

can_delete = False if platform.system() == "Windows" else True


def write_doc(results, response):
    delete = False if platform.system() == "Windows" else True
    with tempfile.NamedTemporaryFile(delete=delete) as output:
        # for result in ress:
        output.write(results)
        output.flush()
        output = open(output.name, "+br")
        response.write(output.read())
    return response
