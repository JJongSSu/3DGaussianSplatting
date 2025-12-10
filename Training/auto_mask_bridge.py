from ultralytics import YOLOWorld, SAM
import cv2
import os
import numpy as np
import argparse
from pathlib import Path
import torch

def process_images(input_dir, output_dir, prompt="concrete bridge"):
    print(f"Initializing models... (Prompt: '{prompt}')")

    # 1. YOLO-World 로드 (텍스트로 객체 위치 탐지)
    # 처음 실행 시 모델 파일을 자동으로 다운로드합니다.
    det_model = YOLOWorld('yolov8x-worldv2.pt')
    det_model.set_classes([prompt])

    # 2. SAM 로드 (박스 기반 정밀 마스킹)
    seg_model = SAM('sam_b.pt')

    os.makedirs(output_dir, exist_ok=True)
    input_path = Path(input_dir)

    # jpg, png, JPG, PNG 등 대소문자 구분 없이 찾기
    files = sorted([f for f in input_path.iterdir() if f.suffix.lower() in ['.jpg', '.png', '.jpeg']])

    print(f"Found {len(files)} images in {input_dir}")
    print("Starting auto-masking process. This may take a while...")

    for i, file in enumerate(files):
        try:
            # A. YOLO-World로 교각 위치(Box) 탐지
            det_results = det_model.predict(str(file), conf=0.05, verbose=False)

            img = cv2.imread(str(file))
            if img is None: continue

            # 탐지된 것이 없으면 검은색(또는 원본) 저장
            if len(det_results[0].boxes) == 0:
                print(f"[{i+1}/{len(files)}] No '{prompt}' detected in {file.name}. Saving black image.")
                black_img = np.zeros_like(img)
                cv2.imwrite(str(Path(output_dir) / file.name), black_img)
                continue

            # B. 탐지된 박스 좌표 가져오기
            bboxes = det_results[0].boxes.xyxy.cpu().numpy()

            # C. SAM으로 박스 내부의 정밀한 누끼(Mask) 따기
            # ultralytics SAM은 bboxes 인자를 받아 해당 영역만 세그멘테이션합니다.
            seg_results = seg_model(str(file), bboxes=bboxes, verbose=False)

            # 여러 개의 마스크가 나올 수 있으므로 하나로 합치기
            combined_mask = np.zeros(img.shape[:2], dtype=bool)

            if seg_results[0].masks is not None:
                for mask in seg_results[0].masks.data:
                    m = mask.cpu().numpy().astype(bool)
                    # 크기가 맞지 않을 경우를 대비해 리사이즈 (보통은 맞음)
                    if m.shape != combined_mask.shape:
                        m = cv2.resize(m.astype(np.uint8), (combined_mask.shape[1], combined_mask.shape[0])).astype(bool)
                    combined_mask |= m

            # D. 배경 제거 (마스크가 아닌 부분은 검은색 처리)
            # 3DGS는 검은색 배경을 '빈 공간'으로 인식하기 유리합니다.
            img[~combined_mask] = [0, 0, 0]

            # 저장
            output_file = Path(output_dir) / file.name
            cv2.imwrite(str(output_file), img)
            print(f"[{i+1}/{len(files)}] Processed {file.name}")

        except Exception as e:
            print(f"Error processing {file.name}: {e}")

    print(f"\nDone! Masked images are saved in: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, required=True, help='Path to original input images folder')
    parser.add_argument('--output', type=str, required=True, help='Path to save masked images')
    parser.add_argument('--prompt', type=str, default='concrete bridge', help='Text prompt for detection (e.g. "bridge", "pillar")')

    args = parser.parse_args()
    process_images(args.input, args.output, args.prompt)
