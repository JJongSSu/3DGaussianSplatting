# Gaussian Splatting Unity Example

이 프로젝트는 **3D Gaussian Splatting**의 학습 파이프라인과 **Unity** 뷰어/연동 환경을 포함하고 있는 예제 프로젝트입니다.

## 📂 프로젝트 구조 (Project Structure)

*   **Root (Unity Project)**: Unity 기반의 Gaussian Splatting 뷰어 및 에셋 관리
    *   `Assets/`: Unity 스크립트 및 씬 파일
*   **Training/**: Python 기반의 Gaussian Splatting 학습 및 데이터 처리 파이프라인
    *   `setup_environment.bat`: 학습 환경 설정 스크립트
    *   `run_pipeline.bat`: 동영상 처리 및 학습 파이프라인 실행 스크립트
    *   `train_gaussian.py`: Gaussian Splatting 학습 스크립트

## ⚙️ 설치 및 환경 설정 (Installation)

이 프로젝트의 학습 파이프라인을 실행하기 위해서는 **NVIDIA GPU**와 **Windows** 환경이 권장됩니다.

### 1. 필수 요구사항
*   **Python 3.8 이상**: [Python 다운로드](https://www.python.org/downloads/)
*   **CUDA Toolkit (11.8 또는 12.1 권장)**: [CUDA 다운로드](https://developer.nvidia.com/cuda-downloads)
*   **Visual Studio 2019/2022 (C++ 데스크톱 개발)**: CUDA 컴파일을 위해 필요
*   **COLMAP**: SfM(Structure from Motion) 처리를 위해 필요합니다.
    *   [COLMAP 다운로드](https://github.com/colmap/colmap/releases) 후 시스템 환경 변수(PATH)에 등록하거나 경로를 기억해두세요.

### 2. Python 환경 설정
`Training` 폴더 내의 스크립트를 사용하여 필요한 라이브러리와 서브모듈을 설치합니다.

```bash
cd Training
setup_environment.bat
```
이 스크립트는 다음을 자동으로 수행합니다:
*   Pip 업그레이드 및 PyTorch 설치
*   `gaussian-splatting` 원본 리포지토리 및 서브모듈(diff-gaussian-rasterization 등) 설치

## 🚀 사용 방법 (Usage)

### 데이터 전처리 및 학습
동영상을 입력으로 받아 프레임 추출, COLMAP 수행, 그리고 학습까지 진행하려면 `run_pipeline.bat` (또는 `run_full_pipeline.py`)를 사용하세요.

1. `Training` 폴더로 이동합니다.
2. 파이프라인 스크립트를 실행합니다.

```bash
cd Training
# 사용법 예시 (스크립트 내용에 따라 인자가 다를 수 있음)
python run_full_pipeline.py --video_path <비디오_경로> --output_path <결과_저장_경로>
```

### Unity에서 확인
학습된 `.ply` 파일이나 `.splat` 파일을 Unity 프로젝트의 `Assets/StreamingAssets` 또는 지정된 경로로 가져와 시각화할 수 있습니다.


## 🛠️ 단계별 실행 가이드 (Advanced Usage)
전체 파이프라인을 한 번에 실행하지 않고, 각 단계를 개별적으로 제어하고 싶다면 아래 명령어들을 참고하세요.

### 1. 동영상에서 프레임 추출
동영상에서 학습에 사용할 이미지를 추출합니다.

```bash
cd Training
# 10프레임마다 1장 추출 (interval=10)
python extract_frames.py --video "C:/path/to/video.mp4" --output "./projects/my_project" --interval 10
```

### 2. COLMAP SfM 처리
추출된 이미지를 사용하여 카메라 포즈를 추정합니다. COLMAP이 설치되어 있어야 합니다.

```bash
# --data 경로는 'input' 폴더가 있는 상위 폴더를 지정해야 합니다.
python run_colmap.py --data "./projects/my_project" --colmap-path "C:/path/to/colmap.exe"
```

### 3. Gaussian Splatting 학습
COLMAP 처리 결과를 바탕으로 3D Gaussian Splatting 모델을 학습합니다.

```bash
# --source_path는 COLMAP 처리가 완료된 폴더 경로입니다.
python train_gaussian.py --source_path "./projects/my_project" --iterations 30000
```
*   `iterations`: 학습 반복 횟수 (기본값: 30000)
    *   빠른 테스트: 7,000 ~ 10,000
    *   고품질: 30,000 이상

## ⚠️ 주의사항
* 이 프로젝트는 **UnityGaussianSplatting**을 기반으로 합니다. 원본 리포지토리를 Clone 하여 시작할 수 있습니다.
```bash
git clone https://github.com/aras-p/UnityGaussianSplatting.git
git clone https://github.com/graphdeco-inria/gaussian-splatting.git
```
* gaussian-splatting 서브모듈 설치 참고
```bash
$env:CUDA_HOME = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4"; conda activate gaussian_splatting;
pip install --no-build-isolation submodules/diff-gaussian-rasterization
pip install --no-build-isolation submodules/simple-knn submodules/fused-ssim
python -c "from diff_gaussian_rasterization import GaussianRasterizer; from simple_knn._C import distCUDA2; import fused_ssim; print('모든 모듈 import 성공!')"
```
*   학습 데이터와 결과물(`output/`, `projects/`)은 용량이 크기 때문에 `.gitignore`에 등록되어 GitHub에 업로드되지 않습니다.
*   `gaussian-splatting` 폴더는 학습 시 자동으로 클론되거나 생성되므로 저장소에서 제외되어 있습니다.
