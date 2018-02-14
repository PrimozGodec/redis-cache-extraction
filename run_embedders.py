import os
from orangecontrib.imageanalytics.image_embedder import ImageEmbedder


def run_embeddings(model, image_dir):
    image_file_paths = [os.path.join(dr, ff) for dr, _, ffs in os.walk(image_dir)
                        for ff in ffs if ff not in ["index.html", "README.md"]]
    print(image_file_paths)

    print("#of pics: {0}".format(len(image_file_paths)))

    with ImageEmbedder(model=model, layer='penultimate') as embedder:
        embedder.clear_cache()
        embeddings = embedder(image_file_paths)
        print(embeddings)


if __name__ == "__main__":
    run_embeddings("inception-v3")