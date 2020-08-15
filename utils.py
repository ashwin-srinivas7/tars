import os
import secrets
import pandas as pd
import io
from flaskblog import app
from PIL import Image
from flask import send_file


def save_text_file(form_text_file):
    random_hex = secrets.token_hex(8)  # rename picture to random 8-bit hex value
    _, f_ext = os.path.splitext(form_text_file.filename)  # obtain the file extension from form
    text_filename = random_hex + f_ext  # create new filename
    file_path = os.path.join(app.root_path, 'static/text_files', text_filename)  # set new relative path
    form_text_file.save(dst=file_path, buffer_size=1024)

    return text_filename


def save_picture(form_picture, directory):
    """
    Function to save picture to the server. Sets name and path for picture to be uploaded to the server
    :param directory:
    :param form_picture: picture data from the form
    :return: modified name of picture

    """
    random_hex = secrets.token_hex(8)  # rename picture to random 8-bit hex value
    _, f_ext = os.path.splitext(form_picture.filename)  # obtain the file extension from form
    picture_filename = random_hex + f_ext  # create new filename for picture
    picture_path = os.path.join(app.root_path, 'static/{}'.format(directory), picture_filename)  # set path for
    # picture file

    # resize picture to 125x125 pixels to reduce size before saving it to the server
    output_size = (125, 125)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(picture_path)  # save picture in the specified path

    return picture_filename


def get_file_contents(file_name):
    file_location = os.path.join(app.root_path, 'static', 'text_files', file_name)

    # open file and read its contents
    with open(file_location.__str__(), encoding="utf-8") as file:
        data = file.read().replace('\n', ' ')

    return str(data)


def get_dataframe(data):
    df_test = pd.DataFrame([data], columns=['data'])
    return df_test


def get_download_csv(file, f_name):

    f_name = str(f_name)

    # Create a string buffer
    buf_str = io.StringIO(file)

    # Create a bytes buffer from the string buffer
    buf_byt = io.BytesIO(buf_str.read().encode("utf-8"))

    # Return the CSV data as an attachment
    return send_file(buf_byt,
                     mimetype="text/csv",
                     as_attachment=True,
                     attachment_filename="{}.csv".format(f_name))
