@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ============================================================
echo 3D Gaussian Splatting - 동영상에서 PLY 생성
echo ============================================================
echo.

REM 동영상 파일 입력 받기
if "%~1"=="" (
    @REM set /p VIDEO_PATH="동영상 파일 경로를 입력하세요: "
    set VIDEO_PATH="D:\Project\GaussianSplatting\projects\GaussianExample\Training\video\20250701_125100.mp4"
) else (
    set VIDEO_PATH=%~1
)

REM 동영상 파일 존재 확인
if not exist "!VIDEO_PATH!" (
    echo [오류] 동영상 파일을 찾을 수 없습니다: !VIDEO_PATH!
    pause
    exit /b 1
)

REM 프로젝트 이름 설정
for %%F in ("!VIDEO_PATH!") do set PROJECT_NAME=%%~nF
set OUTPUT_DIR=.\projects\!PROJECT_NAME!

echo.
echo 동영상: !VIDEO_PATH!
echo 프로젝트 폴더: !OUTPUT_DIR!
echo.

REM COLMAP 경로 설정 (CUDA 버전은 COLMAP.bat 사용)
set COLMAP_PATH=D:\colmap-x64-windows-cuda\COLMAP.bat
if not exist "!COLMAP_PATH!" (
    echo [오류] COLMAP을 찾을 수 없습니다: !COLMAP_PATH!
    pause
    exit /b 1
)
echo COLMAP 경로: !COLMAP_PATH!

echo.
echo ============================================================
echo Step 1/3: 프레임 추출
echo ============================================================
python extract_frames.py --video "!VIDEO_PATH!" --output "!OUTPUT_DIR!" --interval 10 --max-frames 300 --resize-width 1920

if errorlevel 1 (
    echo [오류] 프레임 추출 실패
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Step 2/3: COLMAP 전처리
echo ============================================================
python run_colmap.py --data "!OUTPUT_DIR!" --colmap-path "!COLMAP_PATH!"

if errorlevel 1 (
    echo [오류] COLMAP 전처리 실패
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Step 3/3: 3D Gaussian Splatting 학습
echo ============================================================
python train_gaussian.py --source_path "!OUTPUT_DIR!" --gs_path ".\gaussian-splatting" --iterations 15000 -r 2

if errorlevel 1 (
    echo [오류] 학습 실패
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 완료!
echo ============================================================
echo.
echo PLY 파일 위치: !OUTPUT_DIR!\output\point_cloud\iteration_15000\point_cloud.ply
echo.
echo Unity에서 사용:
echo   Tools - Gaussian Splats - Create GaussianSplatAsset
echo   Input PLY/SPZ File에 위 경로의 PLY 파일 선택
echo.
pause

