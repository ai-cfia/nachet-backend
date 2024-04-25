import microscope.microscope_info as m

path=r"/workspaces/nachet-backend/docs/asssets/image/test_02.jpg"

def test_print_exif_info():
    data = m.get_picture_details(path)

    for key, value in data.items():
        print(f"{key:25} : {value}")
