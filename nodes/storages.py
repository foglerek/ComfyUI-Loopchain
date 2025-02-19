import torch
from torch.utils.data import DataLoader
from server import PromptServer
from aiohttp import web
import random
from PIL import Image, ImageOps
from PIL.PngImagePlugin import PngInfo
import numpy as np
import folder_paths
from torch.utils.data import DataLoader
import os

GLOBAL_IMAGE_STORAGE = {}
GLOBAL_LATENT_STORAGE = {}

class ImageStorageImport:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": { "key": ("STRING", {"multiline": False}), "image": ("IMAGE", ) }
        }

    CATEGORY = "Loopchain/storage"
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "execute"

    def execute(self, key, image):
        if key not in GLOBAL_IMAGE_STORAGE:
            GLOBAL_IMAGE_STORAGE[key] = []
        GLOBAL_IMAGE_STORAGE[key].append(image)
        return {}

    @classmethod
    def IS_CHANGED():
        return float("nan")

class ImageStorageExportLoop:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "key": ("STRING", {"multiline": False}),
                "batch_size": ("INT", {"default": 1000, "min": 1}),
                "loop_idx": ("INT", {"default": 0, "min": 0}),
                "loop_end": ("INT", {"default": 0, "min": 0}),
            },
            "optional": {
                "opt_pipeline": ("LOOPCHAIN_PIPELINE", )
            }
        }

    CATEGORY = "Loopchain/storage"
    FUNCTION = "execute"
    RETURN_TYPES = ("IMAGE", "INT", "INT")
    RETURN_NAMES = ("IMAGE", "LOOP IDX (INT)", "IDX_IN_BATCH (INT)")

    def execute(self, key, batch_size, loop_idx, loop_end, opt_pipeline=None):
        key = key.strip()
        assert GLOBAL_IMAGE_STORAGE[key], f"Image storage {key} doesn't exist."
        dataloader = DataLoader(torch.cat(GLOBAL_IMAGE_STORAGE[key], dim=0), batch_size=batch_size)
        return (list(dataloader)[loop_idx], loop_idx, loop_idx % batch_size)

    @classmethod
    def IS_CHANGED():
        return float("nan")

class ImageStorageExport:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "key": ("STRING", {"multiline": False}),
            },
            "optional": {
                "opt_pipeline": ("LOOPCHAIN_PIPELINE", )
            }
        }

    CATEGORY = "Loopchain/storage"
    FUNCTION = "execute"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGE",)

    def execute(self, key, opt_pipeline=None):
        key = key.strip()
        assert GLOBAL_IMAGE_STORAGE[key], f"Image storage {key} doesn't exist."
        return (torch.cat(GLOBAL_IMAGE_STORAGE[key], dim=0),)

    @classmethod
    def IS_CHANGED():
        return float("nan")

class ImageStorageReset:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": { "key_list": ("STRING", {"multiline": True, "default": '*'}) },
            "optional": {
                "pipeline": ("LOOPCHAIN_PIPELINE", )
            }
        }

    CATEGORY = "Loopchain/storage"
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "execute"

    def execute(self, key_list):
        keys = GLOBAL_IMAGE_STORAGE.keys() if key_list.strip() == '*' else ','.split(key_list)
        keys = list(map(lambda key: key.strip(), keys))
        for key in keys:
            if key in GLOBAL_IMAGE_STORAGE:
                del GLOBAL_IMAGE_STORAGE[key.strip()]
        return {}

    @classmethod
    def IS_CHANGED():
        return float("nan")



IMAGE_EXTENSIONS = ('.ras', '.xwd', '.bmp', '.jpe', '.jpg', '.jpeg', '.xpm', '.ief', '.pbm', '.tif', '.gif', '.ppm', '.xbm', '.tiff', '.rgb', '.pgm', '.png', '.pnm', 'webp')

class ImageToImageStorage:
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {
                "key": ("STRING", {"multiline": False}),
                "image": (sorted(files), {"image_upload": True})
            },
            "optional": {
                "pipeline": ("LOOPCHAIN_PIPELINE", )
            }
        }

    CATEGORY = "Loopchain/storage"
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "load_image"

    def load_image(self, key, image):
        key = key.strip()
        image_path = folder_paths.get_annotated_filepath(image)
        i = Image.open(image_path)
        i = ImageOps.exif_transpose(i)
        image = i.convert("RGB")
        image = np.array(image).astype(np.float32) / 255.0
        image = torch.from_numpy(image)[None,]

        GLOBAL_IMAGE_STORAGE[key] = [image]

        return ()

    @classmethod
    def IS_CHANGED(s, key, image):
        image_path = folder_paths.get_annotated_filepath(image)
        m = hashlib.sha256()
        with open(image_path, 'rb') as f:
            m.update(f.read())
        return m.digest().hex()

    @classmethod
    def VALIDATE_INPUTS(s, key, image):
        if not folder_paths.exists_annotated_filepath(image):
            return "Invalid image file: {}".format(image)

        return True


class FolderToImageStorage:
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        folders = [f for f in os.listdir(input_dir) if not os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {
                "key": ("STRING", {"multiline": False}),
                "folder": (sorted(folders), )
            },
            "optional": {
                "pipeline": ("LOOPCHAIN_PIPELINE", )
            }
        }

    CATEGORY = "Loopchain/storage"
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "load_image"

    def load_image(self, key, folder):
        key = key.strip()
        folder = os.path.join(folder_paths.get_input_directory(), folder)
        images = filter(lambda f: os.path.splitext(f)[1] in IMAGE_EXTENSIONS, os.listdir(folder))
        images = sorted(list(images))

        assert len(images), "No image is found in folder {folder}"

        GLOBAL_IMAGE_STORAGE[key] = []

        for image_name in images:
            i = Image.open(os.path.join(folder_paths.get_input_directory(), folder, image_name))
            i = ImageOps.exif_transpose(i)
            image = i.convert("RGB")
            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None,]

            GLOBAL_IMAGE_STORAGE[key].append(image)

        return {}











class LatentStorageImport:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": { "key": ("STRING", {"multiline": False}), "latent": ("LATENT", ) }
        }

    CATEGORY = "Loopchain/storage"
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "execute"

    def execute(self, key, latent):
        key = key.strip()
        if key not in GLOBAL_LATENT_STORAGE:
            GLOBAL_LATENT_STORAGE[key] = []

        num_samples = len(latent["samples"])
        num_noise_masks = len(latent["noise_mask"])

        chunked_samples = latent["samples"].chunk(num_samples, dim=0)
        chunked_noise_mask = latent["noise_mask"].chunk(num_noise_masks, dim=0)

        for idx, sample in enumerate(chunked_samples):
            noise_mask = chunked_noise_mask[idx] if idx < num_noise_masks else chunked_noise_mask[0]
            GLOBAL_LATENT_STORAGE[key].append({
                "samples": sample,
                "noise_mask": noise_mask
            })

        return {}

    @classmethod
    def IS_CHANGED():
        return float("nan")

class LatentStorageExportLoop:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "key": ("STRING", {"multiline": False}),
                "batch_size": ("INT", {"default": 1000, "min": 1}),
                "loop_idx": ("INT", {"default": 0, "min": 0}),
                "loop_end": ("INT", {"default": 0, "min": 0}),
            },
            "optional": {
                "opt_pipeline": ("LOOPCHAIN_PIPELINE", )
            }
        }

    CATEGORY = "Loopchain/storage"
    FUNCTION = "execute"
    RETURN_TYPES = ("LATENT", "INT", "INT")
    RETURN_NAMES = ("LATENT", "LOOP IDX (INT)", "IDX_IN_BATCH (INT)")

    def execute(self, key, batch_size, loop_idx, loop_end, opt_pipeline=None):
        key = key.strip()
        assert GLOBAL_LATENT_STORAGE[key], f"Latent storage {key} doesn't exist."
        return (GLOBAL_LATENT_STORAGE[key][loop_idx], loop_idx, loop_idx % batch_size)

    @classmethod
    def IS_CHANGED():
        return float("nan")

class LatentStorageReset:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": { "key_list": ("STRING", {"multiline": True, "default": '*'}) },
            "optional": {
                "pipeline": ("LOOPCHAIN_PIPELINE", )
            }
        }

    CATEGORY = "Loopchain/storage"
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "execute"

    def execute(self, key_list):
        keys = GLOBAL_LATENT_STORAGE.keys() if key_list.strip() == '*' else ','.split(key_list)
        keys = list(map(lambda key: key.strip(), keys))
        for key in keys:
            if key in GLOBAL_LATENT_STORAGE:
                del GLOBAL_LATENT_STORAGE[key.strip()]
        return {}

    @classmethod
    def IS_CHANGED():
        return float("nan")


NODE_CLASS_MAPPINGS = {
    "ImageStorageImport": ImageStorageImport,
    "ImageStorageExportLoop": ImageStorageExportLoop,
    "ImageStorageExport": ImageStorageExport,
    "ImageStorageReset": ImageStorageReset,
    "ImageToImageStorage": ImageToImageStorage,
    "FolderToImageStorage": FolderToImageStorage,
    "LatentStorageImport": LatentStorageImport,
    "LatentStorageExportLoop": LatentStorageExportLoop,
    "LatentStorageReset": LatentStorageReset
}

@PromptServer.instance.routes.get("/loopchain/dataloader_length")
async def get_storage_length(request):
    storage_type = request.query["type"]
    storage_key = request.query["key"].strip()
    batch_size = int(request.query["batch_size"])

    storage =  GLOBAL_IMAGE_STORAGE if storage_type == "image" else GLOBAL_LATENT_STORAGE
    if not storage_key in storage:
        return web.json_response({
            "result": -1
        })

    if storage_type == "image":
        dataloader = DataLoader(torch.cat(storage[storage_key], dim=0), batch_size=batch_size)
        return web.json_response({
            "result": len(dataloader)
        })

    if storage_type == "latent":
        return web.json_response({
            "result": len(storage[storage_key])
        })

    return None
