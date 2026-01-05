#!/usr/bin/env python3

import httpx
import json
from typing import Optional

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def test_endpoint(name: str, method: str, url: str, headers: Optional[dict] = None, 
                  data: Optional[dict] = None, expected_status: int = 200):
    """测试单个端点"""
    try:
        with httpx.Client(timeout=30.0) as client:
            if method.upper() == "GET":
                response = client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = client.post(url, headers=headers, json=data)
            elif method.upper() == "PATCH":
                response = client.patch(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = client.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = client.delete(url, headers=headers)
            else:
                print_error(f"不支持的HTTP方法: {method}")
                return False, None
            
            if response.status_code == expected_status:
                print_success(f"{name} - Status: {response.status_code}")
                return True, response
            else:
                print_error(f"{name} - 期望状态码 {expected_status}, 实际 {response.status_code}")
                print_error(f"响应: {response.text[:200]}")
                return False, response
    except Exception as e:
        print_error(f"{name} - 错误: {str(e)}")
        return False, None

def main():
    print_info("=" * 60)
    print_info("开始测试所有API端点")
    print_info("=" * 60)
    print()
    
    # 存储token
    access_token = None
    refresh_token = None
    admin_token = None
    
    # ============================================================================
    # 1. 公共端点（无需认证）
    # ============================================================================
    print_info("\n【1. 公共端点测试】")
    print("-" * 60)
    
    # 健康检查
    success, response = test_endpoint(
        "GET / - 健康检查",
        "GET",
        f"{BASE_URL}/"
    )
    
    # 搜索 - 按坐标
    print()
    print_info("测试搜索功能...")
    success, response = test_endpoint(
        "POST /api/stores/search - 按坐标搜索",
        "POST",
        f"{BASE_URL}/api/stores/search",
        data={
            "location": {
                "latitude": 42.3601,
                "longitude": -71.0589
            },
            "filters": {
                "radius_miles": 10.0
            }
        }
    )
    
    # ============================================================================
    # 2. 认证端点
    # ============================================================================
    print_info("\n【2. 认证端点测试】")
    print("-" * 60)
    
    # 登录 - Admin
    print()
    print_info("测试Admin登录...")
    success, response = test_endpoint(
        "POST /api/auth/login - Admin登录",
        "POST",
        f"{BASE_URL}/api/auth/login",
        data={
            "email": "admin@test.com",
            "password": "TestPassword123!"
        },
        expected_status=200
    )
    
    if success and response:
        try:
            tokens = response.json()
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")
            print_success(f"获取到 access_token: {access_token[:20]}...")
            print_success(f"获取到 refresh_token: {refresh_token[:20]}...")
            admin_token = access_token
        except:
            print_error("无法解析登录响应")
    
    # 刷新token
    if refresh_token:
        print()
        print_info("测试token刷新...")
        success, response = test_endpoint(
            "POST /api/auth/refresh - 刷新token",
            "POST",
            f"{BASE_URL}/api/auth/refresh",
            data={
                "refresh_token": refresh_token
            },
            expected_status=200
        )
        if success and response:
            try:
                new_tokens = response.json()
                new_access_token = new_tokens.get("access_token")
                print_success(f"获取到新的 access_token: {new_access_token[:20]}...")
                access_token = new_access_token  # 使用新token
            except:
                print_warning("无法解析刷新响应")
    
    # ============================================================================
    # 3. 商店管理端点（需要认证）
    # ============================================================================
    if not admin_token:
        print_error("\n无法获取认证token，跳过需要认证的测试")
        return
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    print_info("\n【3. 商店管理端点测试】")
    print("-" * 60)
    
    # 创建商店
    print()
    print_info("测试创建商店...")
    test_store_id = "S9999"
    success, response = test_endpoint(
        "POST /api/admin/stores - 创建商店",
        "POST",
        f"{BASE_URL}/api/admin/stores",
        headers=headers,
        data={
            "store_id": test_store_id,
            "name": "测试商店",
            "store_type": "regular",
            "status": "active",
            "latitude": 42.3601,
            "longitude": -71.0589,
            "address_street": "123 Test St",
            "address_city": "Boston",
            "address_state": "MA",
            "address_postal_code": "02101",
            "address_country": "USA",
            "phone": "617-555-9999",
            "services": ["pharmacy"],
            "hours_mon": "08:00-22:00",
            "hours_tue": "08:00-22:00",
            "hours_wed": "08:00-22:00",
            "hours_thu": "08:00-22:00",
            "hours_fri": "08:00-22:00",
            "hours_sat": "09:00-21:00",
            "hours_sun": "10:00-20:00"
        },
        expected_status=200
    )
    
    # 列出商店
    print()
    print_info("测试列出商店...")
    success, response = test_endpoint(
        "GET /api/admin/stores - 列出商店（分页）",
        "GET",
        f"{BASE_URL}/api/admin/stores?page=1&page_size=10",
        headers=headers
    )
    
    # 获取商店详情
    print()
    print_info("测试获取商店详情...")
    success, response = test_endpoint(
        f"GET /api/admin/stores/{test_store_id} - 获取商店详情",
        "GET",
        f"{BASE_URL}/api/admin/stores/{test_store_id}",
        headers=headers
    )
    
    # 更新商店
    print()
    print_info("测试更新商店...")
    success, response = test_endpoint(
        f"PATCH /api/admin/stores/{test_store_id} - 部分更新商店",
        "PATCH",
        f"{BASE_URL}/api/admin/stores/{test_store_id}",
        headers=headers,
        data={
            "name": "更新后的测试商店",
            "phone": "617-555-8888"
        },
        expected_status=200
    )
    
    # 搜索商店（公共端点，但测试一下）
    print()
    print_info("测试搜索商店（公共端点）...")
    success, response = test_endpoint(
        "POST /api/stores/search - 搜索商店（带服务过滤）",
        "POST",
        f"{BASE_URL}/api/stores/search",
        data={
            "location": {
                "latitude": 42.3601,
                "longitude": -71.0589
            },
            "filters": {
                "radius_miles": 10.0,
                "services": ["pharmacy"],
                "store_types": ["regular"]
            }
        }
    )
    
    # ============================================================================
    # 4. CSV导入测试
    # ============================================================================
    print_info("\n【4. CSV导入测试】")
    print("-" * 60)
    
    print()
    print_info("测试CSV导入...")
    csv_content = """store_id,name,store_type,status,latitude,longitude,address_street,address_city,address_state,address_postal_code,address_country,phone,services,hours_mon,hours_tue,hours_wed,hours_thu,hours_fri,hours_sat,hours_sun
S8888,CSV导入测试商店,regular,active,42.3601,-71.0589,456 CSV St,Boston,MA,02101,USA,617-555-7777,pharmacy|pickup,08:00-22:00,08:00-22:00,08:00-22:00,08:00-22:00,08:00-22:00,09:00-21:00,10:00-20:00"""
    
    try:
        files = {'file': ('test.csv', csv_content.encode(), 'text/csv')}
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{BASE_URL}/api/admin/stores/import",
                headers=headers,
                files=files
            )
        if response.status_code == 200:
            print_success(f"POST /api/admin/stores/import - CSV导入 - Status: {response.status_code}")
            result = response.json()
            print_info(f"  导入结果: 总计 {result.get('total_rows')}, 创建 {result.get('created')}, 更新 {result.get('updated')}, 失败 {result.get('failed')}")
        else:
            print_error(f"POST /api/admin/stores/import - 期望状态码 200, 实际 {response.status_code}")
            print_error(f"响应: {response.text[:200]}")
    except Exception as e:
        print_error(f"CSV导入测试 - 错误: {str(e)}")
    
    # ============================================================================
    # 5. 用户管理端点（Admin only）
    # ============================================================================
    print_info("\n【5. 用户管理端点测试】")
    print("-" * 60)
    
    # 列出用户
    print()
    print_info("测试列出用户...")
    success, response = test_endpoint(
        "GET /api/admin/users - 列出所有用户",
        "GET",
        f"{BASE_URL}/api/admin/users",
        headers=headers
    )
    
    # 创建用户
    print()
    print_info("测试创建用户...")
    test_user_id = "U9999"
    success, response = test_endpoint(
        "POST /api/admin/users - 创建用户",
        "POST",
        f"{BASE_URL}/api/admin/users",
        headers=headers,
        data={
            "user_id": test_user_id,
            "email": "testuser@test.com",
            "password": "TestPassword123!",
            "role": "viewer"
        },
        expected_status=200
    )
    
    # 更新用户
    if success:
        print()
        print_info("测试更新用户...")
        success, response = test_endpoint(
            f"PUT /api/admin/users/{test_user_id} - 更新用户",
            "PUT",
            f"{BASE_URL}/api/admin/users/{test_user_id}",
            headers=headers,
            data={
                "role": "marketer",
                "status": "active"
            },
            expected_status=200
        )
    
    # ============================================================================
    # 6. 权限测试（测试不同角色的访问权限）
    # ============================================================================
    print_info("\n【6. 权限测试】")
    print("-" * 60)
    
    # 测试Viewer角色（应该不能创建商店）
    print()
    print_info("测试Viewer角色权限（应该不能创建商店）...")
    success, viewer_response = test_endpoint(
        "POST /api/auth/login - Viewer登录",
        "POST",
        f"{BASE_URL}/api/auth/login",
        data={
            "email": "viewer@test.com",
            "password": "TestPassword123!"
        },
        expected_status=200
    )
    
    if success and viewer_response:
        try:
            viewer_tokens = viewer_response.json()
            viewer_token = viewer_tokens.get("access_token")
            viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
            
            # Viewer应该不能创建商店
            print()
            print_info("测试Viewer尝试创建商店（应该失败）...")
            success, response = test_endpoint(
                "POST /api/admin/stores - Viewer创建商店（应该被拒绝）",
                "POST",
                f"{BASE_URL}/api/admin/stores",
                headers=viewer_headers,
                data={
                    "store_id": "S9998",
                    "name": "Viewer测试商店",
                    "store_type": "regular",
                    "status": "active",
                    "latitude": 42.3601,
                    "longitude": -71.0589,
                    "address_street": "123 Test St",
                    "address_city": "Boston",
                    "address_state": "MA",
                    "address_postal_code": "02101",
                    "address_country": "USA",
                    "phone": "617-555-9999",
                    "services": [],
                    "hours_mon": "08:00-22:00",
                    "hours_tue": "08:00-22:00",
                    "hours_wed": "08:00-22:00",
                    "hours_thu": "08:00-22:00",
                    "hours_fri": "08:00-22:00",
                    "hours_sat": "09:00-21:00",
                    "hours_sun": "10:00-20:00"
                },
                expected_status=403  # 应该返回403 Forbidden
            )
            if response and response.status_code == 403:
                print_success("权限控制正常工作：Viewer无法创建商店")
        except:
            print_warning("无法测试Viewer权限")
    
    # ============================================================================
    # 7. 清理测试数据
    # ============================================================================
    print_info("\n【7. 清理测试数据】")
    print("-" * 60)
    
    # 删除测试商店
    print()
    print_info("删除测试商店...")
    success, response = test_endpoint(
        f"DELETE /api/admin/stores/{test_store_id} - 删除（停用）商店",
        "DELETE",
        f"{BASE_URL}/api/admin/stores/{test_store_id}",
        headers=headers,
        expected_status=200
    )
    
    # 删除测试用户
    print()
    print_info("删除测试用户...")
    success, response = test_endpoint(
        f"DELETE /api/admin/users/{test_user_id} - 删除（停用）用户",
        "DELETE",
        f"{BASE_URL}/api/admin/users/{test_user_id}",
        headers=headers,
        expected_status=200
    )
    
    # ============================================================================
    # 8. 注销
    # ============================================================================
    print_info("\n【8. 注销测试】")
    print("-" * 60)
    
    if refresh_token:
        print()
        print_info("测试注销...")
        success, response = test_endpoint(
            "POST /api/auth/logout - 注销",
            "POST",
            f"{BASE_URL}/api/auth/logout",
            headers=headers,
            data={
                "refresh_token": refresh_token
            },
            expected_status=200
        )
    
    # ============================================================================
    # 总结
    # ============================================================================
    print()
    print_info("=" * 60)
    print_info("所有端点测试完成！")
    print_info("=" * 60)
    print()
    print_info("访问 http://localhost:8000/docs 查看完整的API文档")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print_error(f"\n测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

