"""
3D Gaussian Splatting 학습 실행 스크립트
gaussian-splatting 레포지토리를 사용하여 학습을 수행합니다.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def check_gaussian_splatting_repo(gs_path: str) -> bool:
    """gaussian-splatting 레포지토리가 설치되어 있는지 확인합니다."""
    gs_train_path = Path(gs_path) / "train.py"
    return gs_train_path.exists()


def clone_gaussian_splatting(target_path: str):
    """gaussian-splatting 레포지토리를 클론합니다."""
    print("\n3D Gaussian Splatting 레포지토리 클론 중...")
    
    cmd = [
        "git", "clone",
        "https://github.com/graphdeco-inria/gaussian-splatting.git",
        "--recursive",
        target_path
    ]
    
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print("오류: 레포지토리 클론 실패")
        return False
    
    print("레포지토리 클론 완료!")
    return True


def setup_gaussian_splatting(gs_path: str):
    """gaussian-splatting 환경을 설정합니다."""
    print("\n3D Gaussian Splatting 환경 설정 중...")
    
    gs_path = Path(gs_path)
    
    # submodules 확인
    submodules_path = gs_path / "submodules"
    if not submodules_path.exists() or not list(submodules_path.iterdir()):
        print("서브모듈 초기화 중...")
        subprocess.run(["git", "submodule", "update", "--init", "--recursive"], cwd=str(gs_path))
    
    # diff-gaussian-rasterization 설치
    diff_raster_path = submodules_path / "diff-gaussian-rasterization"
    if diff_raster_path.exists():
        print("diff-gaussian-rasterization 설치 중...")
        subprocess.run([sys.executable, "-m", "pip", "install", str(diff_raster_path)])
    
    # simple-knn 설치
    simple_knn_path = submodules_path / "simple-knn"
    if simple_knn_path.exists():
        print("simple-knn 설치 중...")
        subprocess.run([sys.executable, "-m", "pip", "install", str(simple_knn_path)])
    
    print("환경 설정 완료!")


def run_training(
    source_path: str,
    gs_path: str,
    output_path: str = None,
    iterations: int = 30000,
    save_iterations: list = None,
    resolution: int = -1,
    sh_degree: int = 3
):
    """
    3D Gaussian Splatting 학습을 실행합니다.
    
    Args:
        source_path: COLMAP 처리된 데이터 경로
        gs_path: gaussian-splatting 레포지토리 경로
        output_path: 출력 경로 (기본값: source_path/output)
        iterations: 학습 반복 횟수
        save_iterations: PLY 저장할 반복 횟수들
        resolution: 이미지 해상도 다운스케일 (-1: 원본, 2: 1/2, 4: 1/4)
        sh_degree: Spherical Harmonics 차수 (0~3)
    """
    
    source_path = Path(source_path).resolve()
    gs_path = Path(gs_path).resolve()
    
    if output_path is None:
        output_path = source_path / "output"
    else:
        output_path = Path(output_path).resolve()
    
    if save_iterations is None:
        save_iterations = [7000, 15000, 30000]
    
    # 학습 스크립트 경로
    train_script = gs_path / "train.py"
    
    if not train_script.exists():
        print(f"오류: train.py를 찾을 수 없습니다 - {train_script}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("3D Gaussian Splatting 학습 시작")
    print("=" * 60)
    print(f"\n설정:")
    print(f"  - 소스 데이터: {source_path}")
    print(f"  - 출력 경로: {output_path}")
    print(f"  - 학습 반복: {iterations}")
    print(f"  - PLY 저장 시점: {save_iterations}")
    
    # 학습 명령어 구성
    save_iter_str = " ".join(map(str, save_iterations))
    
    cmd = [
        sys.executable, str(train_script),
        "-s", str(source_path),
        "-m", str(output_path),
        "--iterations", str(iterations),
        "--save_iterations", *map(str, save_iterations),
        "-r", str(resolution),
        "--sh_degree", str(sh_degree)
    ]
    
    print(f"\n명령어: {' '.join(cmd)}")
    print("\n학습 시작... (시간이 오래 걸릴 수 있습니다)")
    print("-" * 60)
    
    # 학습 실행
    result = subprocess.run(cmd, cwd=str(gs_path))
    
    if result.returncode != 0:
        print(f"\n오류: 학습 실패 (종료 코드: {result.returncode})")
        sys.exit(1)
    
    # 결과 확인
    print("\n" + "=" * 60)
    print("학습 완료!")
    print("=" * 60)
    
    # PLY 파일 위치 안내
    for iter_num in save_iterations:
        ply_path = output_path / f"point_cloud" / f"iteration_{iter_num}" / "point_cloud.ply"
        if ply_path.exists():
            file_size = ply_path.stat().st_size / (1024 * 1024)
            print(f"\nPLY 파일 생성됨:")
            print(f"  - 경로: {ply_path}")
            print(f"  - 크기: {file_size:.1f} MB")
    
    final_ply = output_path / "point_cloud" / f"iteration_{iterations}" / "point_cloud.ply"
    print(f"\n최종 PLY 파일: {final_ply}")
    print("\n이 파일을 Unity의 GaussianSplat 에셋 생성에 사용하세요!")
    print("  Unity: Tools → Gaussian Splats → Create GaussianSplatAsset")


def main():
    parser = argparse.ArgumentParser(
        description="3D Gaussian Splatting 학습 실행"
    )
    parser.add_argument(
        "--source_path", "-s",
        type=str,
        required=True,
        help="COLMAP 처리된 데이터 경로"
    )
    parser.add_argument(
        "--gs_path", "-g",
        type=str,
        default="./gaussian-splatting",
        help="gaussian-splatting 레포지토리 경로 (기본값: ./gaussian-splatting)"
    )
    parser.add_argument(
        "--output_path", "-o",
        type=str,
        default=None,
        help="출력 경로 (기본값: source_path/output)"
    )
    parser.add_argument(
        "--iterations", "-i",
        type=int,
        default=30000,
        help="학습 반복 횟수 (기본값: 30000)"
    )
    parser.add_argument(
        "--resolution", "-r",
        type=int,
        default=-1,
        help="이미지 해상도 다운스케일 팩터 (1, 2, 4, 8 등)"
    )
    parser.add_argument(
        "--sh_degree",
        type=int,
        default=3,
        help="Spherical Harmonics 차수 (0-3)"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="gaussian-splatting 환경 설정 실행"
    )
    parser.add_argument(
        "--clone",
        action="store_true",
        help="gaussian-splatting 레포지토리 클론"
    )
    
    args = parser.parse_args()
    
    gs_path = Path(args.gs_path).resolve()
    
    # 레포지토리 클론
    if args.clone or not check_gaussian_splatting_repo(str(gs_path)):
        if not gs_path.exists():
            clone_gaussian_splatting(str(gs_path))
        else:
            print(f"경로가 이미 존재합니다: {gs_path}")
    
    # 환경 설정
    if args.setup:
        setup_gaussian_splatting(str(gs_path))
        return
    
    # 학습 실행
    if not check_gaussian_splatting_repo(str(gs_path)):
        print(f"오류: gaussian-splatting 레포지토리를 찾을 수 없습니다.")
        print(f"  --clone 옵션으로 레포지토리를 클론하세요.")
        sys.exit(1)
    
    run_training(
        source_path=args.source_path,
        gs_path=str(gs_path),
        output_path=args.output_path,
        iterations=args.iterations,
        resolution=args.resolution,
        sh_degree=args.sh_degree
    )


if __name__ == "__main__":
    main()

