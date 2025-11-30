#!/usr/bin/env python3
"""
로컬 프로젝트 분석 유틸리티
GitHub 분석 코드를 파일시스템 기반으로 수정
"""
import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


def analyze_project_structure(project_path: str, extensions: List[str] = ['py']) -> Dict[str, Any]:
    """
    프로젝트 전체의 폴더, py파일, 각 py파일의 클래스명, 함수명을 트리 구조로 반환하는 함수
    
    Args:
        project_path: 분석할 프로젝트 루트 경로
        extensions: 분석할 파일 확장자 리스트
        
    Returns:
        dict: 파일 구조 정보
            - file_count: 찾은 파일 개수
            - structure: 트리 구조 문자열
    """
    project_path = Path(project_path).resolve()
    
    # 모든 대상 파일 찾기
    all_files = []
    for ext in extensions:
        for file_path in project_path.rglob(f'*.{ext}'):
            # __pycache__, .git 등 제외
            if not any(part.startswith('.') or part == '__pycache__' 
                      for part in file_path.parts):
                relative_path = file_path.relative_to(project_path)
                all_files.append(str(relative_path))
    
    # 정렬
    all_files.sort()
    
    # 각 파일의 함수/클래스 정보 수집
    file_info = {}
    for file_path in all_files:
        full_path = project_path / file_path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            functions, classes = _extract_functions_and_classes(content)
            file_info[file_path] = {
                'functions': functions,
                'classes': classes
            }
        except Exception as e:
            file_info[file_path] = {
                'functions': [],
                'classes': {}
            }
    
    # 트리 구조 생성
    structure = _build_tree_structure(all_files, file_info)
    
    return {
        "file_count": len(all_files),
        "structure": structure
    }


def extract_code_contents(project_path: str, targets: List[str]) -> Dict[str, Any]:
    """
    읽고싶은 py파일, 클래스명, 함수명을 list로 주면 그 부분만 읽어서 한번에 반환하는 함수
    
    Args:
        project_path: 프로젝트 루트 경로
        targets: 추출할 대상 리스트
            - "파일경로": 전체 파일 내용
            - "파일경로:클래스명": 특정 클래스만
            - "파일경로:함수명": 특정 함수만
            
    Returns:
        dict: 각 타겟별 추출 결과
    """
    project_path = Path(project_path).resolve()
    results = {}
    
    for target in targets:
        try:
            # 타겟 파싱
            if ':' in target:
                file_path, item_name = target.split(':', 1)
            else:
                file_path = target
                item_name = None
            
            full_path = project_path / file_path
            
            # 파일 읽기
            if not full_path.exists():
                results[target] = {
                    "error": f"파일을 찾을 수 없습니다: {file_path}"
                }
                continue
                
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if item_name:
                # 특정 함수/클래스만 추출
                extracted = _extract_specific_item(content, item_name)
                if extracted:
                    results[target] = {
                        "type": "class_or_function",
                        "path": file_path,
                        "item": item_name,
                        "content": extracted
                    }
                else:
                    results[target] = {
                        "error": f"'{item_name}'을 찾을 수 없습니다"
                    }
            else:
                # 전체 파일
                results[target] = {
                    "type": "file",
                    "path": file_path,
                    "content": content
                }
                
        except Exception as e:
            results[target] = {
                "error": str(e)
            }
    
    return results


def _extract_functions_and_classes(content: str) -> Tuple[List[Tuple[str, int]], Dict[str, Dict]]:
    """Python 코드에서 함수와 클래스 정의를 추출"""
    try:
        tree = ast.parse(content)
        functions = []  # [(name, line_no), ...]
        classes = {}    # {name: {'line': line_no, 'methods': [(name, line_no), ...]}}
        
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                functions.append((node.name, node.lineno))
            elif isinstance(node, ast.ClassDef):
                class_methods = []
                for class_node in node.body:
                    if isinstance(class_node, ast.FunctionDef):
                        class_methods.append((class_node.name, class_node.lineno))
                classes[node.name] = {
                    'line': node.lineno,
                    'methods': class_methods
                }
        
        return functions, classes
        
    except Exception:
        # AST 파싱 실패시 정규식 사용
        lines = content.split('\n')
        functions = []
        classes = {}
        current_class = None
        
        for i, line in enumerate(lines, 1):
            # 함수 정의
            func_match = re.match(r'^def\s+(\w+)', line)
            if func_match:
                func_name = func_match.group(1)
                if current_class and line.startswith('    '):
                    # 클래스 메소드
                    classes[current_class]['methods'].append((func_name, i))
                else:
                    # 모듈 레벨 함수
                    functions.append((func_name, i))
                    current_class = None
                    
            # 클래스 정의
            class_match = re.match(r'^class\s+(\w+)', line)
            if class_match:
                class_name = class_match.group(1)
                current_class = class_name
                classes[class_name] = {'line': i, 'methods': []}
                
            # 들여쓰기가 없는 줄이면 현재 클래스 범위 벗어남
            if line and not line[0].isspace():
                if not func_match and not class_match:
                    current_class = None
        
        return functions, classes


def _extract_specific_item(content: str, name: str) -> Optional[str]:
    """특정 함수나 클래스의 내용 추출"""
    lines = content.split('\n')
    result_lines = []
    in_target = False
    indent_level = 0
    
    for i, line in enumerate(lines):
        # 함수나 클래스 정의 찾기
        if re.match(rf'^(def|class)\s+{re.escape(name)}\s*[\(:]', line):
            in_target = True
            indent_level = len(line) - len(line.lstrip())
            result_lines.append(line)
        elif in_target:
            # 현재 줄의 들여쓰기 확인
            if line.strip() == '':
                # 빈 줄은 포함
                result_lines.append(line)
            elif line and len(line) - len(line.lstrip()) <= indent_level:
                # 같거나 낮은 들여쓰기면 종료
                break
            else:
                # 더 깊은 들여쓰기면 포함
                result_lines.append(line)
    
    return '\n'.join(result_lines) if result_lines else None


def _build_tree_structure(file_paths: List[str], file_info: Dict[str, Dict]) -> str:
    """파일 경로 리스트로부터 트리 구조 생성"""
    def get_tree_dict(paths):
        tree = {}
        for path in paths:
            parts = Path(path).parts
            current = tree
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]
        return tree
    
    def print_tree(tree, prefix="", is_last=True, current_path=""):
        items = list(tree.items())
        output_lines = []
        
        for i, (name, subtree) in enumerate(items):
            is_last_item = i == len(items) - 1
            full_path = f"{current_path}/{name}" if current_path else name
            
            # 파일인지 확인
            if '.' in name and not subtree:
                output_lines.append(
                    f"{prefix}{'└── ' if is_last_item else '├── '}📄 {name}"
                )
                
                # Python 파일이면 함수/클래스 정보 표시
                if name.endswith('.py') and full_path in file_info:
                    info = file_info[full_path]
                    extension = "    " if is_last_item else "│   "
                    
                    # 클래스와 메소드
                    for class_name, class_info in info.get('classes', {}).items():
                        if isinstance(class_info, dict):
                            line_no = class_info.get('line', 0)
                            methods = class_info.get('methods', [])
                            if methods:
                                method_strs = [f"{m[0]}:{m[1]}" for m in methods]
                                output_lines.append(
                                    f"{prefix}{extension}🏛️  Class {class_name}:{line_no} [{', '.join(method_strs)}]"
                                )
                            else:
                                output_lines.append(
                                    f"{prefix}{extension}🏛️  Class {class_name}:{line_no}"
                                )
                    
                    # 모듈 레벨 함수
                    if info.get('functions'):
                        func_strs = [f"{f[0]}:{f[1]}" for f in info['functions']]
                        output_lines.append(
                            f"{prefix}{extension}⚙️  Functions: {', '.join(func_strs)}"
                        )
            else:
                # 디렉토리
                output_lines.append(
                    f"{prefix}{'└── ' if is_last_item else '├── '}📁 {name}/"
                )
                extension = "    " if is_last_item else "│   "
                output_lines.extend(
                    print_tree(subtree, prefix + extension, is_last_item, full_path)
                )
        
        return output_lines
    
    # 트리 생성
    tree = get_tree_dict(file_paths)
    tree_lines = print_tree(tree)
    
    # 결과 포맷팅
    result = "프로젝트 구조:\n"
    result += "-" * 78 + "\n"
    result += "\n".join(tree_lines)
    result += "\n" + "-" * 78
    
    return result


if __name__ == "__main__":
    # 테스트용
    import sys
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
        
        # 구조 분석
        structure = analyze_project_structure(project_path)
        print(structure['structure'])
        print(f"\n총 {structure['file_count']}개 파일 발견")
        
        # 특정 항목 추출 테스트
        if len(sys.argv) > 2:
            targets = sys.argv[2:]
            contents = extract_code_contents(project_path, targets)
            for target, result in contents.items():
                print(f"\n--- {target} ---")
                if 'error' in result:
                    print(f"오류: {result['error']}")
                else:
                    print(f"타입: {result['type']}")
                    print(f"경로: {result['path']}")
                    if 'item' in result:
                        print(f"항목: {result['item']}")
                    print("내용:")
                    print(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])