#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 Ollama 连接和模型可用性
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json

def test_ollama():
    print("=" * 60)
    print("测试 Ollama 服务连接")
    print("=" * 60)
    
    # 测试服务是否可用
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama 服务可用")
            data = response.json()
            print(f"\n可用模型列表:")
            for model in data.get("models", []):
                print(f"  - {model['name']} ({model.get('size', 'unknown')})")
        else:
            print(f"❌ Ollama 服务返回错误: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("❌ 连接超时，请确认 Ollama 服务正在运行")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到 Ollama 服务")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    
    return True

def test_model_generation(model_name="qwen3:8b"):
    print(f"\n{'=' * 60}")
    print(f"测试模型生成能力: {model_name}")
    print("=" * 60)
    
    test_prompt = "请用一句话介绍你自己。"
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": test_prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            print(f"✅ 模型响应成功")
            print(f"响应内容: {generated_text[:200]}...")
            return True
        else:
            print(f"❌ 模型生成失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    # 测试连接
    if test_ollama():
        # 测试模型生成
        test_model_generation("qwen3:8b")
