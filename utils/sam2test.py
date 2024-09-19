import os

import numpy as np
from sam2.build_sam import build_sam2_video_predictor
import matplotlib.pyplot as plt
from PIL import Image
import torch

checkpoint = "../segment-anything-2/checkpoints/sam2_hiera_large.pt"
model_cfg = "sam2_hiera_l.yaml"
predictor = build_sam2_video_predictor(model_cfg, checkpoint)


def show_mask(mask, ax, obj_id=None, random_color=False):
    if random_color:
        color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    else:
        cmap = plt.get_cmap("tab10")
        cmap_idx = 0 if obj_id is None else obj_id
        color = np.array([*cmap(cmap_idx)[:3], 0.6])
    h, w = mask.shape[-2:]
    mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    ax.imshow(mask_image)

def show_points(coords, labels, ax, marker_size=200):
    pos_points = coords[labels == 1]
    neg_points = coords[labels == 0]
    ax.scatter(pos_points[:, 0], pos_points[:, 1], color='green', marker='*', s=marker_size, edgecolor='white',
               linewidth=1.25)
    ax.scatter(neg_points[:, 0], neg_points[:, 1], color='red', marker='*', s=marker_size, edgecolor='white',
               linewidth=1.25)


def show_box(box, ax):
    x0, y0 = box[0], box[1]
    w, h = box[2] - box[0], box[3] - box[1]
    ax.add_patch(plt.Rectangle((x0, y0), w, h, edgecolor='green', facecolor=(0, 0, 0, 0), lw=2))


def run():
    video_dir = "../../MarioKartCV/video/2023-06-02 20-49-54"

    # scan all the JPEG frame names in this directory
    frame_names = [
        p for p in os.listdir(video_dir)
        if os.path.splitext(p)[-1] in [".jpg", ".jpeg", ".JPG", ".JPEG"]
    ]
    frame_names.sort(key=lambda p: int(os.path.splitext(p)[0]))

    # frame_idx = 2583
    frame_idx = 0
    plt.figure(figsize=(9, 6))
    plt.title(f"frame {frame_idx}")
    plt.imshow(Image.open(os.path.join(video_dir, frame_names[frame_idx])))
    plt.show(block=True)

    ann_frame_idx = frame_idx  # the frame index we interact with
    ann_obj_id = frame_idx  # give a unique id to each object we interact with (it can be any integers)

    # Let's add a positive click at (x, y) = (210, 350) to get started
    # , [450, 500]
    points = np.array([[500, 700], [460, 630], [500, 630], [490, 750]], dtype=np.float32)
    # for labels, `1` means positive click and `0` means negative click
    labels = np.array([1, 0, 1, 1], np.int32)

    print('we boutta start torchin')
    # with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
    #     print('yo we torchin')
    state = predictor.init_state(video_path=video_dir)

    # add new prompts and instantly get the output on the same frame
    print('adding points')
    _, out_obj_ids, out_mask_logits = predictor.add_new_points_or_box(
        inference_state=state,
        frame_idx=ann_frame_idx,
        obj_id=ann_obj_id,
        points=points,
        labels=labels
    )
    print("added points")

    # show the results on the current (interacted) frame
    plt.figure(figsize=(9, 6))
    plt.title(f"frame {ann_frame_idx}")
    plt.imshow(Image.open(os.path.join(video_dir, frame_names[ann_frame_idx])))
    show_points(points, labels, plt.gca())
    show_mask((out_mask_logits[0] > 0.0).cpu().numpy(), plt.gca(), obj_id=out_obj_ids[0])
    plt.show()

    # propagate the prompts to get masklets throughout the video
    for frame_idx, object_ids, masks in predictor.propagate_in_video(state):
        if frame_idx > 10:
            break
        print(f'frame {frame_idx}')
        plt.imshow(Image.open(os.path.join(video_dir, frame_names[frame_idx])))
        show_mask((masks[0] > 0.0).cpu().numpy(), plt.gca(), obj_id=object_ids[0])
        plt.show()


if __name__ == "__main__":
    run()
