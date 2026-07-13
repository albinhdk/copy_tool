# tests/test_file_service.py
import pytest
import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.file_service import FileService

@pytest.fixture
def file_service():
    """创建FileService实例"""
    return FileService()

@pytest.fixture
def temp_dirs():
    """创建临时源目录和目标目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = os.path.join(tmpdir, "source")
        tgt_dir = os.path.join(tmpdir, "target")
        os.makedirs(src_dir)
        os.makedirs(tgt_dir)
        
        # 创建测试文件结构
        os.makedirs(os.path.join(src_dir, "subdir"))
        with open(os.path.join(src_dir, "file1.txt"), "w") as f:
            f.write("content1")
        with open(os.path.join(src_dir, "subdir", "file2.txt"), "w") as f:
            f.write("content2")
        
        yield src_dir, tgt_dir

def test_copy_files_success(file_service, temp_dirs):
    """测试成功拷贝文件"""
    src_dir, tgt_dir = temp_dirs
    files = ["file1.txt", "subdir/file2.txt"]
    
    success_count, errors = file_service.copy_files(src_dir, tgt_dir, files)
    
    assert success_count == 2
    assert len(errors) == 0
    assert os.path.exists(os.path.join(tgt_dir, "file1.txt"))
    assert os.path.exists(os.path.join(tgt_dir, "subdir", "file2.txt"))
    
    # 验证内容
    with open(os.path.join(tgt_dir, "file1.txt")) as f:
        assert f.read() == "content1"

def test_copy_files_preserve_structure(file_service, temp_dirs):
    """测试保持目录结构"""
    src_dir, tgt_dir = temp_dirs
    files = ["subdir/file2.txt"]
    
    success_count, errors = file_service.copy_files(src_dir, tgt_dir, files)
    
    assert success_count == 1
    assert os.path.exists(os.path.join(tgt_dir, "subdir", "file2.txt"))

def test_copy_files_strip_configured_structure_root_for_all_types(file_service):
    """结构起点对所有文件类型生效。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = os.path.join(tmpdir, "source")
        tgt_dir = os.path.join(tmpdir, "target")
        os.makedirs(os.path.join(src_dir, "nms", "src", "views", "station", "hub"))
        os.makedirs(os.path.join(src_dir, "src", "components"))
        os.makedirs(tgt_dir)

        with open(os.path.join(src_dir, "nms", "src", "views", "station", "hub", "Hub.vue"), "w") as f:
            f.write("<template>hub</template>")
        with open(os.path.join(src_dir, "src", "components", "Header.vue"), "w") as f:
            f.write("<template>header</template>")

        with open(os.path.join(src_dir, "src", "components", "helper.ts"), "w") as f:
            f.write("export default {}")

        files = ["src/components/Header.vue", "src/components/helper.ts"]
        success_count, errors = file_service.copy_files(
            src_dir, tgt_dir, files, structure_root="src"
        )

        assert success_count == 2
        assert len(errors) == 0
        assert os.path.exists(os.path.join(tgt_dir, "components", "Header.vue"))
        assert os.path.exists(os.path.join(tgt_dir, "components", "helper.ts"))
        assert not os.path.exists(os.path.join(tgt_dir, "src"))


def test_files_outside_structure_root_keep_repository_path(file_service):
    """结构起点外的文件仍按仓库相对路径复制。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = os.path.join(tmpdir, "source")
        tgt_dir = os.path.join(tmpdir, "target")
        os.makedirs(os.path.join(src_dir, "src", "utils"))
        os.makedirs(tgt_dir)

        with open(os.path.join(src_dir, "src", "utils", "helper.js"), "w") as f:
            f.write("export default {}")

        with open(os.path.join(src_dir, "pom.xml"), "w") as f:
            f.write("<project />")

        files = ["src/utils/helper.js", "pom.xml"]
        success_count, errors = file_service.copy_files(
            src_dir, tgt_dir, files, structure_root="src"
        )

        assert success_count == 2
        assert os.path.exists(os.path.join(tgt_dir, "utils", "helper.js"))
        assert os.path.exists(os.path.join(tgt_dir, "pom.xml"))


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        (["src/views/Home.vue", "src/api/user.ts"], "src"),
        (["src/main/java/com/demo/App.java", "pom.xml"], "src/main/java"),
        (["src/main/java/com/demo/App.java", "src/main/resources/app.yml"], "src/main"),
        (["app/src/main/java/com/demo/App.java"], "app/src/main/java"),
        (["README.md"], ""),
    ],
)
def test_detect_structure_root(file_service, files, expected):
    """自动识别覆盖常见前端、Maven 和 Gradle 目录。"""
    assert file_service.detect_structure_root(files) == expected


def test_copy_stops_before_output_path_collision(file_service):
    """裁剪路径与仓库路径冲突时不复制任何文件。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = os.path.join(tmpdir, "source")
        tgt_dir = os.path.join(tmpdir, "target")
        os.makedirs(os.path.join(src_dir, "src", "config"))
        os.makedirs(os.path.join(src_dir, "config"))
        os.makedirs(tgt_dir)
        for path in ("src/config/app.yml", "config/app.yml"):
            full_path = os.path.join(src_dir, *path.split("/"))
            with open(full_path, "w") as f:
                f.write(path)

        success_count, errors = file_service.copy_files(
            src_dir,
            tgt_dir,
            ["src/config/app.yml", "config/app.yml"],
            structure_root="src",
        )

        assert success_count == 0
        assert len(errors) == 1
        assert "路径冲突" in errors[0]
        assert os.listdir(tgt_dir) == []


def test_copy_files_nonexistent(file_service, temp_dirs):
    """测试拷贝不存在的文件"""
    src_dir, tgt_dir = temp_dirs
    files = ["nonexistent.txt"]
    
    success_count, errors = file_service.copy_files(src_dir, tgt_dir, files)
    
    assert success_count == 0
    assert len(errors) == 0  # 不存在的文件被静默跳过

def test_clear_directory(file_service, temp_dirs):
    """测试清空目录"""
    _, tgt_dir = temp_dirs
    
    # 创建一些文件
    with open(os.path.join(tgt_dir, "test.txt"), "w") as f:
        f.write("test")
    os.makedirs(os.path.join(tgt_dir, "subdir"))
    
    file_service.clear_directory(tgt_dir)
    
    # 验证目录为空
    assert len(os.listdir(tgt_dir)) == 0

def test_clear_nonexistent_directory(file_service):
    """测试清空不存在的目录"""
    # 应该不抛出异常
    file_service.clear_directory("/nonexistent/path")
