#!/usr/bin/env python3
"""
简单对话功能测试脚本
专门测试基础对话接口的功能
"""
import requests
import json
import time
import sys
from datetime import datetime

class ChatSimpleTest:
    """简单对话测试器"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session_id = f"simple_test_{int(time.time())}"
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, message: str = "", response_data: dict = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")
        print()
        
    def send_chat_message(self, message: str, session_id: str = None) -> tuple:
        """发送对话消息"""
        url = f"{self.base_url}/api/chat"
        data = {
            "message": message,
            "session_id": session_id or self.session_id
        }
        
        try:
            response = requests.post(url, json=data, timeout=30)
            return True, response.status_code, response.json()
        except requests.exceptions.ConnectionError:
            return False, 0, {"error": "连接失败，请确保Flask服务器正在运行"}
        except requests.exceptions.Timeout:
            return False, 0, {"error": "请求超时"}
        except Exception as e:
            return False, 0, {"error": str(e)}
    
    def test_basic_chat(self):
        """测试基础对话功能"""
        print("🔍 测试基础对话功能...")
        
        test_message = "你好，这是一个测试消息"
        success, status_code, response = self.send_chat_message(test_message)
        
        if success and status_code == 200 and response.get('success'):
            data = response.get('data', {})
            reply = data.get('reply', '')
            if reply:
                self.log_result(
                    "基础对话功能",
                    True,
                    f"收到回复: {reply[:50]}{'...' if len(reply) > 50 else ''}",
                    data
                )
            else:
                self.log_result("基础对话功能", False, "回复为空", response)
        else:
            error_msg = response.get('error', '未知错误') if isinstance(response, dict) else str(response)
            self.log_result("基础对话功能", False, f"请求失败: {error_msg}", response)
    
    def test_empty_message(self):
        """测试空消息处理"""
        print("🔍 测试空消息处理...")
        
        success, status_code, response = self.send_chat_message("")
        
        if success and status_code == 400:
            self.log_result("空消息处理", True, "正确返回400错误", response)
        else:
            self.log_result("空消息处理", False, f"应该返回400错误，实际: {status_code}", response)
    
    def test_long_message(self):
        """测试长消息处理"""
        print("🔍 测试长消息处理...")
        
        long_message = "这是一个很长的测试消息。" * 100  # 约1000字符
        success, status_code, response = self.send_chat_message(long_message)
        
        if success and status_code == 200 and response.get('success'):
            data = response.get('data', {})
            reply = data.get('reply', '')
            if reply:
                self.log_result("长消息处理", True, f"成功处理长消息，回复长度: {len(reply)}", data)
            else:
                self.log_result("长消息处理", False, "长消息处理后回复为空", response)
        else:
            error_msg = response.get('error', '未知错误') if isinstance(response, dict) else str(response)
            self.log_result("长消息处理", False, f"长消息处理失败: {error_msg}", response)
    
    def test_special_characters(self):
        """测试特殊字符处理"""
        print("🔍 测试特殊字符处理...")
        
        special_message = "测试特殊字符：😀🎉🔥 @#$%^&*() 中文English 123"
        success, status_code, response = self.send_chat_message(special_message)
        
        if success and status_code == 200 and response.get('success'):
            data = response.get('data', {})
            reply = data.get('reply', '')
            if reply:
                self.log_result("特殊字符处理", True, "成功处理特殊字符", data)
            else:
                self.log_result("特殊字符处理", False, "特殊字符处理后回复为空", response)
        else:
            error_msg = response.get('error', '未知错误') if isinstance(response, dict) else str(response)
            self.log_result("特殊字符处理", False, f"特殊字符处理失败: {error_msg}", response)
    
    def test_different_session_ids(self):
        """测试不同会话ID"""
        print("🔍 测试不同会话ID...")
        
        session1 = "test_session_1"
        session2 = "test_session_2"
        
        # 在两个不同会话中发送消息
        success1, status1, response1 = self.send_chat_message("我是会话1", session1)
        success2, status2, response2 = self.send_chat_message("我是会话2", session2)
        
        if (success1 and status1 == 200 and response1.get('success') and
            success2 and status2 == 200 and response2.get('success')):
            self.log_result("不同会话ID", True, "成功处理不同会话ID", {
                "session1_reply": response1.get('data', {}).get('reply', '')[:30],
                "session2_reply": response2.get('data', {}).get('reply', '')[:30]
            })
        else:
            self.log_result("不同会话ID", False, "处理不同会话ID失败", {
                "session1": response1,
                "session2": response2
            })
    
    def test_response_format(self):
        """测试响应格式"""
        print("🔍 测试响应格式...")
        
        success, status_code, response = self.send_chat_message("测试响应格式")
        
        if success and status_code == 200:
            # 检查必要字段
            required_fields = ['success', 'data']
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields and response.get('success'):
                data = response.get('data', {})
                data_fields = ['reply', 'session_id', 'timestamp']
                missing_data_fields = [field for field in data_fields if field not in data]
                
                if not missing_data_fields:
                    self.log_result("响应格式", True, "响应格式正确", response)
                else:
                    self.log_result("响应格式", False, f"数据字段缺失: {missing_data_fields}", response)
            else:
                self.log_result("响应格式", False, f"必要字段缺失: {missing_fields}", response)
        else:
            self.log_result("响应格式", False, f"请求失败，状态码: {status_code}", response)
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始简单对话功能测试")
        print("=" * 50)
        print(f"测试目标: {self.base_url}")
        print(f"会话ID: {self.session_id}")
        print("=" * 50)
        
        # 运行各项测试
        self.test_basic_chat()
        self.test_empty_message()
        self.test_long_message()
        self.test_special_characters()
        self.test_different_session_ids()
        self.test_response_format()
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("=" * 50)
        print("📊 简单对话测试报告")
        print("=" * 50)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['success'])
        failed = total - passed
        
        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"成功率: {passed/total*100:.1f}%")
        print()
        
        if failed > 0:
            print("❌ 失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['message']}")
            print()
        
        # 保存详细报告
        import os
        report_dir = "Agent/test"
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        
        report_file = f"{report_dir}/chat_simple_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"📄 详细报告已保存到: {report_file}")
        print("=" * 50)

def main():
    """主函数"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
    
    tester = ChatSimpleTest(base_url)
    tester.run_all_tests()

if __name__ == '__main__':
    main()