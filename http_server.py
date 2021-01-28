import socket
import sys
import traceback
import mimetypes
import os
import ast

WEBROOT = os.environ.get("WEBROOT", "./webroot")

PYTHON_MIMETYPE = 'script/python'
mimetypes.add_type(PYTHON_MIMETYPE, '.py')
mimetypes.add_type(PYTHON_MIMETYPE, '.pyc')

def response_ok(body=b"This is a minimal response", mimetype=b"text/plain"):
    """
    returns a basic HTTP response
    Ex:
        response_ok(
            b"<html><h1>Welcome:</h1></html>",
            b"text/html"
        ) ->

        b'''
        HTTP/1.1 200 OK\r\n
        Content-Type: text/html\r\n
        \r\n
        <html><h1>Welcome:</h1></html>\r\n
        '''
    """

    return b"HTTP/1.1 200 OK\r\n" \
           b"Content-Type: " + mimetype + b"\r\n"\
           b"\r\n" \
           b"" + body


def response_method_not_allowed():
    """Returns a 405 Method Not Allowed response"""

    return b'''HTTP/1.1 405 OK\r\n
               Content-Type: text/html\r\n
               \r\n
               Method not allowed!'''


def response_not_found():
    """Returns a 404 Not Found response"""

    return b"HTTP/1.1 404 OK\r\n" \
           b"\r\n" \
           b"Not Found"


def parse_request(request):
    """
    Given the content of an HTTP request, returns the path of that request.

    This server only handles GET requests, so this method shall raise a
    NotImplementedError if the method of the request is not GET.
    """
    header = request.split("\r\n")[0]
    method, path, protocol = header.split(" ")

    if not "GET" in method:
        raise NotImplementedError

    return path

def eval_pyton_script(script_path: str):
    """
    run the script and get the return
    encode the return for the server response processing
    :return: bytes
    """
    result = os.popen(f"python {script_path}", 'r').read().encode('utf8')
    return result

def response_path(path):
    """
    This method should return appropriate content and a mime type.

    If the requested path is a directory, then the content should be a
    plain-text listing of the contents with mimetype `text/plain`.

    If the path is a file, it should return the contents of that file
    and its correct mimetype.

    If the path does not map to a real location, it should raise an
    exception that the server can catch to return a 404 response.

    Ex:
        response_path('/a_web_page.html') -> (b"<html><h1>North Carolina...",
                                            b"text/html")

        response_path('/images/sample_1.png')
                        -> (b"A12BCF...",  # contents of sample_1.png
                            b"image/png")

        response_path('/') -> (b"images/, a_web_page.html, make_type.py,...",
                             b"text/plain")

        response_path('/a_page_that_doesnt_exist.html') -> Raises a NameError

    """

    content = b"not implemented"
    mime_type = b"not implemented"

    file_path = WEBROOT + path

    if os.path.exists(file_path):
        # Fill in the appropriate content and mime_type give the path.
        if os.path.isdir(file_path):
            mime_type = b""
            content = get_folder(file_path)

        elif os.path.isfile(file_path):
            mime_type = mimetypes.MimeTypes().guess_type(file_path)[0].encode('utf8')
            if mime_type == PYTHON_MIMETYPE.encode('utf8'):
                # If the path is "make_time.py", then you may OPTIONALLY return the
                # result of executing `make_time.py`. But you need only return the
                # CONTENTS of `make_time.py`.
                mime_type = b"text/html"
                content = eval_pyton_script(file_path)
            else:
                content = open(file_path, 'rb').read()
    else:
        # Raise a NameError if the requested content is not present
        # under webroot.
        raise NameError

    return content, mime_type


def get_folder(path):
    path_list = b""
    for path in os.listdir(path):
        path_list += path.encode('utf8') + b"\n"
    return path_list

def server(log_buffer=sys.stderr):
    address = ('127.0.0.1', 10000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("making a server on {0}:{1}".format(*address), file=log_buffer)
    sock.bind(address)
    sock.listen(1)

    try:
        while True:
            print('waiting for a connection', file=log_buffer)
            conn, addr = sock.accept()  # blocking
            try:
                print('connection - {0}:{1}'.format(*addr), file=log_buffer)

                request = ''
                while True:
                    data = conn.recv(1024)
                    request += data.decode('utf8')

                    if '\r\n\r\n' in request:
                        break

                print("Request received:\n{}\n\n".format(request))

                try:
                    # If parse_request raised a NotImplementedError, then let
                    # response be a method_not_allowed response. If response_path raised
                    # a NameError, then let response be a not_found response. Else,
                    # use the content and mimetype from response_path to build a
                    # response_ok.
                    path = parse_request(request=request)

                    body, mimetype = response_path(path=path)

                    response = response_ok(body=body,
                                           mimetype=mimetype)
                except NotImplementedError:
                    response = response_method_not_allowed()
                except NameError:
                    response = response_not_found()

                # print("responce:\n", response)
                conn.sendall(response)
            except Exception as e:
                traceback.print_exc()
            finally:
                conn.close() 

    except KeyboardInterrupt:
        sock.close()
        return
    except:
        traceback.print_exc()


if __name__ == '__main__':
    server()
    sys.exit(0)


