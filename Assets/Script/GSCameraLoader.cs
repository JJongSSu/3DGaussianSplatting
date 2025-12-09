using System.Collections.Generic;
using UnityEngine;
using System.IO;
using System.Text.RegularExpressions;

public class GSCameraLoader : MonoBehaviour
{
    [Header("Files")]
    [Tooltip("cameras.json 경로를 입력하세요")]
    public string jsonFilePath = "D:/Project/GaussianSplatting/projects/GaussianExample/Assets/Script/Cameras/20250701_124952_cameras.json";

    [Header("Settings")]
    public Camera targetCamera;
    [Tooltip("좌표계 변환을 위한 스케일 (X, Y, Z). 보통 (1, -1, 1) 또는 (1, 1, 1)을 시도해보세요.")]
    public Vector3 positionScale = new Vector3(1, -1, 1);

    [Header("Data")]
    public List<CameraInfo> loadedCameras = new List<CameraInfo>();
    public int selectedIndex = 0;

    [System.Serializable]
    public class CameraInfo
    {
        public int id;
        public string img_name;
        public int width;
        public int height;
        public Vector3 position;
        public Matrix4x4 rotationMatrix;
        public float fov;
    }

    private void Start()
    {
        if (targetCamera == null) targetCamera = Camera.main;
    }

    // JSON 파싱이 복잡할 수 있어 간단한 문자열 처리로 구현 (외부 라이브러리 의존성 제거)
    [ContextMenu("Load Cameras")]
    public void LoadCameras()
    {
        if (!File.Exists(jsonFilePath))
        {
            Debug.LogError($"File not found: {jsonFilePath}");
            return;
        }

        string jsonContent = File.ReadAllText(jsonFilePath);
        loadedCameras.Clear();

        // 정규식으로 각 객체 블록 추출 (간이 파서)
        // 주의: 이 파서는 표준 3DGS output cameras.json 형식을 가정합니다.
        string pattern = @"\{""id"":\s*(\d+),\s*""img_name"":\s*""([^""]+)"".*?""position"":\s*\[([^\]]+)\],\s*""rotation"":\s*\[\[([^\]]+)\],\s*\[([^\]]+)\],\s*\[([^\]]+)\]\].*?""fy"":\s*([0-9\.]+).*?\}";

        foreach (Match match in Regex.Matches(jsonContent, pattern))
        {
            try
            {
                CameraInfo cam = new CameraInfo();
                cam.id = int.Parse(match.Groups[1].Value);
                cam.img_name = match.Groups[2].Value;

                // Position
                string[] posStrs = match.Groups[3].Value.Split(',');
                cam.position = new Vector3(
                    float.Parse(posStrs[0]),
                    float.Parse(posStrs[1]),
                    float.Parse(posStrs[2])
                );

                // Rotation (3x3 Matrix)
                string[] r0 = match.Groups[4].Value.Split(',');
                string[] r1 = match.Groups[5].Value.Split(',');
                string[] r2 = match.Groups[6].Value.Split(',');

                Matrix4x4 m = Matrix4x4.identity;
                m.m00 = float.Parse(r0[0]); m.m01 = float.Parse(r0[1]); m.m02 = float.Parse(r0[2]);
                m.m10 = float.Parse(r1[0]); m.m11 = float.Parse(r1[1]); m.m12 = float.Parse(r1[2]);
                m.m20 = float.Parse(r2[0]); m.m21 = float.Parse(r2[1]); m.m22 = float.Parse(r2[2]);
                cam.rotationMatrix = m;

                // FOV calculation (approximated vertical FOV from fy)
                // height가 JSON 정규식 뒷부분에 있어서 파싱이 복잡하므로,
                // match되지 않은 경우 기본값이나 추가 파싱이 필요할 수 있음.
                // 여기서는 fy값만 가져와서 대략적인 fov를 계산하거나 로그용으로 저장.
                float fy = float.Parse(match.Groups[7].Value);
                // 3DGS JSON에는 height가 앞에 있으므로 다시 파싱하거나, 단순화를 위해
                // FOV는 일단 고정값이나 추후 계산하도록 둡니다.

                loadedCameras.Add(cam);
            }
            catch (System.Exception e)
            {
                Debug.LogWarning($"Error parsing camera entry: {e.Message}");
            }
        }

        Debug.Log($"Loaded {loadedCameras.Count} cameras.");
    }

    [ContextMenu("Apply View")]
    public void ApplySelectedView()
    {
        if (loadedCameras.Count == 0 || selectedIndex < 0 || selectedIndex >= loadedCameras.Count) return;

        CameraInfo info = loadedCameras[selectedIndex];

        // 1. Position Transformation
        // Unity (LHS, Y-up) vs COLMAP (RHS)
        // 보통 3DGS 데이터는 그대로 두고 Unity 상위 오브젝트를 회전시키거나,
        // 좌표를 변환해야 합니다. 여기서는 좌표 변환을 시도합니다.
        Vector3 finalPos = new Vector3(
            info.position.x * positionScale.x,
            info.position.y * positionScale.y,
            info.position.z * positionScale.z
        );

        // 2. Rotation Transformation
        // JSON의 Rotation은 보통 World-to-Camera (View Matrix) 입니다.
        // 우리가 필요한 건 Camera-to-World (Transform.rotation) 입니다.
        // 따라서 Transpose(Inverse for rotation)를 해야 할 수 있습니다.

        // 매트릭스에서 쿼터니언 추출 (기본적인 접근)
        // COLMAP 좌표계를 Unity로 맞추기 위해 Z축 반전 등을 고려해야 함.
        // 가장 쉬운 방법: LookAt을 사용하는 것이지만, Roll이 정확하지 않을 수 있음.
        // 여기서는 매트릭스 컬럼을 기반으로 변환을 시도합니다.

        // COLMAP R is World-to-Camera. We want Camera-to-World.
        Matrix4x4 camToWorld = info.rotationMatrix.transpose; // Or inverse

        // Unity Vector coordinate conversion applied to basis vectors
        Vector3 right = new Vector3(camToWorld.m00, camToWorld.m10, camToWorld.m20);
        Vector3 up    = new Vector3(camToWorld.m01, camToWorld.m11, camToWorld.m21); // COLMAP Y is usually down
        Vector3 fwd   = new Vector3(camToWorld.m02, camToWorld.m12, camToWorld.m22);

        // Apply Coordinate System Fix (Y-up vs Y-down, Z-fwd vs Z-back)
        // 이 부분은 데이터셋과 학습 설정에 따라 다를 수 있어 시행착오가 필요할 수 있습니다.
        // 일반적인 3DGS -> Unity 변환:
        // Position: x, -y, z
        // Rotation: Y축 반전 및 Z축 반전 고려

        if (positionScale.y < 0) // If converting Y-down to Y-up
        {
            right.y = -right.y;
            up.y = -up.y;
            fwd.y = -fwd.y;
        }

        Quaternion rot = Quaternion.LookRotation(fwd, -up); // COLMAP Y is usually 'down', so up is -Y?

        // Apply to Camera
        targetCamera.transform.position = finalPos;
        targetCamera.transform.rotation = rot;

        Debug.Log($"Moved camera to: {info.img_name}");
    }

    private void OnDrawGizmos()
    {
        if (loadedCameras == null) return;
        Gizmos.color = Color.yellow;
        foreach(var cam in loadedCameras)
        {
            Vector3 pos = new Vector3(
                cam.position.x * positionScale.x,
                cam.position.y * positionScale.y,
                cam.position.z * positionScale.z
            );
            Gizmos.DrawSphere(pos, 0.05f);
        }
    }
}