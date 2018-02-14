import json
import os

import paramiko
from PIL.Image import open as open_image, LANCZOS
from io import BytesIO
import hashlib
from PIL import ImageFile
from run_embedders import run_embeddings

MODELS = {
    'inception-v3': {
        'name': 'Inception v3',
        'description': 'Google\'s Inception v3 model trained on ImageNet.',
        'target_image_size': (299, 299),
        'layers': ['penultimate'],
        'order': 0
    },
    'painters': {
        'name': 'Painters',
        'description':
            'A model trained to predict painters from artwork images.',
        'target_image_size': (256, 256),
        'layers': ['penultimate'],
        'order': 3
    },
    'deeploc': {
        'name': 'DeepLoc',
        'description': 'A model trained to analyze yeast cell images.',
        'target_image_size': (64, 64),
        'layers': ['penultimate'],
        'order': 4
    },
    'vgg16': {
        'name': 'VGG-16',
        'description': '16-layer image recognition model trained on ImageNet.',
        'target_image_size': (224, 224),
        'layers': ['penultimate'],
        'order': 1
    },
    'vgg19': {
        'name': 'VGG-19',
        'description': '19-layer image recognition model trained on ImageNet.',
        'target_image_size': (224, 224),
        'layers': ['penultimate'],
        'order': 2
    },
    'openface': {
        'name': 'openface',
        'description': 'Face recognition model trained on FaceScrub and CASIA-WebFace datasets.',
        'target_image_size': (256, 256),
        'layers': ['penultimate'],
        'order': 5
    }
}


def _load_image_from_url_or_local_path(file_path):
    file = file_path

    try:
        return open_image(file)
    except (IOError, ValueError):
        return None


def _load_image_or_none(file_path):
    image = _load_image_from_url_or_local_path(file_path)

    if image is None:
        return image

    if not image.mode == 'RGB':
        try:
            image = image.convert('RGB')
        except ValueError:
            return None

    image.thumbnail(MODELS["inception-v3"]["target_image_size"], LANCZOS)
    image_bytes_io = BytesIO()
    image.save(image_bytes_io, format="JPEG")
    image.close()

    image_bytes_io.seek(0)
    image_bytes = image_bytes_io.read()
    image_bytes_io.close()
    return image_bytes


def md5_hash(bytes_):
    md5 = hashlib.md5()
    md5.update(bytes_)
    return md5.hexdigest()


def gen_redis_proto(*args):
    proto = ''
    proto += '*' + str(len(args)) + '\r\n'
    for arg in args:
        proto += '$' + str(len(bytes(str(arg), 'utf-8'))) + '\r\n'
        proto += str(arg) + '\r\n'
    return proto


ImageFile.LOAD_TRUNCATED_IMAGES = True
images_dir = "images/"

for model, model_server in [
    ("inception-v3", "inception_v3"), ("VGG-16", "vgg16"), ("VGG-19", "vgg19"),
    ("painters", "painters"), ("deeploc", "deeploc")]:

    # call orange to upload all images
    run_embeddings(model, images_dir)

    # generate the cache dump
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.connect("dev.bio.garaza.io", username="primoz")  # this is hyperion
    (stdin, stdout, stderr) = ssh.exec_command(
        "kubectl get pod | grep redis-redis | awk '{print $1;}'")
    container = stdout.readline()[:-1]

    retrieve_command = "kubectl cp default/{}:/bitnami/redis/data/dump.rdb " \
                       "dump.rdb".format(container)

    ssh.exec_command(retrieve_command)
    ssh.close()

    os.system("scp primoz@dev.bio.garaza.io:~/dump.rdb tmp")
    os.system('rdb --command json -k "{}.*" -f tmp/dump.json tmp/dump.rdb'
              .format(model_server))

    # load json
    with open("tmp/dump.json") as f:
        cache = json.load(f)[0]

    datasets = os.walk(images_dir)

    redis_embeddings = []

    for dirpath, dirnames, filenames in datasets:
        for image in filenames:
            if image not in ["index.html", "README.md"]:
                print(os.path.join(dirpath, image))
                im = _load_image_or_none(os.path.join(dirpath, image))
                h = model_server + md5_hash(im)
                redis_embeddings.append("SET")
                redis_embeddings.append(h)
                redis_embeddings.append(cache[h])

    redis_format = gen_redis_proto(*redis_embeddings)
    with open("tmp/redis_proto.txt", "w", encoding="utf-8") as f:
        f.write(redis_format)
