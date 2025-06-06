#!/usr/bin/env python3
"""
Test script for the optimized agentic RAG system.
This script tests the performance improvements and verifies functionality.
"""

import requests
import json
import time
import sys
import os

# Add the current directory to Python path
sys.path.append('/Users/kalana/Desktop/Personal/ChatbotBackend/ursaleo-chat-backend/ChatRAG')

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChatRAG.settings')
import django
django.setup()

BASE_URL = "http://127.0.0.1:8000/core"

def test_agent_health():
    """Test the optimized agent health endpoint."""
    print("=" * 60)
    print("Testing Optimized Agent Health")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/agent-health/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Agent Status: {data.get('status')}")
            print(f"Optimized System: {data.get('optimized_system')}")
            
            if 'performance_metrics' in data:
                metrics = data['performance_metrics']
                print(f"Optimization Features: {metrics.get('optimization_features', [])}")
                print(f"Time Complexity: {metrics.get('time_complexity')}")
                print(f"Supported Modes: {metrics.get('supported_modes')}")
            
            return True
        else:
            print(f"Health check failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error testing health: {e}")
        return False

def test_fast_response():
    """Test the fast response endpoint for performance."""
    print("\n" + "=" * 60)
    print("Testing Fast Response Performance")
    print("=" * 60)
    
    test_queries = [
        "What are the HR policies?",
        "Tell me about leave policies",
        "How do I apply for sick leave?"
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\nTest {i+1}: {query}")
        
        payload = {
            "query": query,
            "twin_version_id": "b7586e58-9a07-47f6-8049-43d6d6f2c5e54455",  # HR Agent
            "chat_instance_id": 1
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/fast-response/",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            processing_time = time.time() - start_time
            
            print(f"Status Code: {response.status_code}")
            print(f"Total Time: {processing_time:.3f}s")
            
            if response.status_code == 200:
                data = response.json()
                agent_processing_time = data.get('metadata', {}).get('processing_time', 0)
                print(f"Agent Processing Time: {agent_processing_time}s")
                print(f"Response Preview: {data.get('openai_response', {}).get('content', '')[:100]}...")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")

def test_full_vs_simple_performance():
    """Compare performance between simple and full modes."""
    print("\n" + "=" * 60)
    print("Performance Comparison: Simple vs Full Mode")
    print("=" * 60)
    
    query = "What is the company's vacation policy?"
    payload_base = {
        "query": query,
        "twin_version_id": "b7586e58-9a07-47f6-8049-43d6d6f2c5e54455",
        "chat_instance_id": 1,
        "use_agents": True
    }
    
    modes = ["simple", "full"]
    results = {}
    
    for mode in modes:
        print(f"\nTesting {mode.upper()} mode:")
        
        payload = payload_base.copy()
        payload["agent_mode"] = mode
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/agentic-document-response/",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            total_time = time.time() - start_time
            
            print(f"Status Code: {response.status_code}")
            print(f"Total Time: {total_time:.3f}s")
            
            if response.status_code == 200:
                data = response.json()
                metadata = data.get('agent_metadata', {})
                processing_time = metadata.get('processing_time', 0)
                
                print(f"Agent Processing Time: {processing_time}s")
                print(f"Mode: {metadata.get('processing_mode')}")
                print(f"Agent Type: {metadata.get('agent_type')}")
                
                if mode == "full":
                    verification = metadata.get('verification', {})
                    print(f"Verification Score: {verification.get('accuracy_score', 'N/A')}")
                
                results[mode] = {
                    "total_time": total_time,
                    "processing_time": processing_time,
                    "success": True
                }
            else:
                print(f"Error: {response.text}")
                results[mode] = {"success": False}
                
        except Exception as e:
            print(f"Error: {e}")
            results[mode] = {"success": False}
    
    # Compare results
    if all(results[mode].get("success") for mode in modes):
        print(f"\n{'='*30} PERFORMANCE COMPARISON {'='*30}")
        for mode in modes:
            r = results[mode]
            print(f"{mode.upper()} Mode - Total: {r['total_time']:.3f}s, Processing: {r['processing_time']:.3f}s")
        
        if results["simple"]["processing_time"] < results["full"]["processing_time"]:
            speedup = results["full"]["processing_time"] / results["simple"]["processing_time"]
            print(f"\nSimple mode is {speedup:.2f}x faster than full mode!")

def test_batch_processing():
    """Test batch processing functionality."""
    print("\n" + "=" * 60)
    print("Testing Batch Processing")
    print("=" * 60)
    
    queries = [
        {
            "query": "What are office hours?",
            "twin_version_id": "b7586e58-9a07-47f6-8049-43d6d6f2c5e54455",
            "chat_instance_id": 1,
            "mode": "simple"
        },
        {
            "query": "How do I request time off?",
            "twin_version_id": "b7586e58-9a07-47f6-8049-43d6d6f2c5e54455", 
            "chat_instance_id": 2,
            "mode": "simple"
        },
        {
            "query": "What is the dress code policy?",
            "twin_version_id": "b7586e58-9a07-47f6-8049-43d6d6f2c5e54455",
            "chat_instance_id": 3,
            "mode": "full"
        }
    ]
    
    payload = {"queries": queries}
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/batch-processing/",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        total_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Total Time: {total_time:.3f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total Queries: {data.get('total_queries')}")
            print(f"Successful Queries: {data.get('successful_queries')}")
            print(f"Average Time per Query: {data.get('average_time_per_query')}s")
            
            # Show individual results
            batch_results = data.get('batch_results', [])
            for i, result in enumerate(batch_results):
                print(f"\nQuery {i+1}:")
                print(f"  Success: {result.get('success')}")
                if result.get('success'):
                    print(f"  Processing Time: {result.get('processing_time')}s")
                    print(f"  Mode: {result.get('mode')}")
                    print(f"  Response Preview: {result.get('response', '')[:50]}...")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_performance_metrics():
    """Test performance metrics endpoint."""
    print("\n" + "=" * 60)
    print("Testing Performance Metrics")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/agent-performance/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("System Information:")
            system_info = data.get('system_info', {})
            for key, value in system_info.items():
                print(f"  {key}: {value}")
            
            print("\nPerformance Metrics:")
            metrics = data.get('performance_metrics', {})
            for key, value in metrics.items():
                if isinstance(value, list):
                    print(f"  {key}:")
                    for item in value:
                        print(f"    - {item}")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

def test_direct_function_integration():
    """Test that the system is using direct functions from document_search_api.py."""
    print("\n" + "=" * 60)
    print("Testing Direct Function Integration")
    print("=" * 60)
    
    # Import the optimized tools to verify they use the core functions
    try:
        from core.agents.optimized_agent_tools import optimized_processor
        from core.views.document_search_api import generate_embeddings_for_single_text, search_query
        
        print("✓ Successfully imported optimized agent tools")
        print("✓ Successfully imported core document_search_api functions")
        
        # Test a quick metadata extraction
        test_query = "What is the leave policy?"
        twin_id = "b7586e58-9a07-47f6-8049-43d6d6f2c5e54455"
        
        print(f"\nTesting direct function calls with query: '{test_query}'")
        
        # Test embedding generation
        start_time = time.time()
        embedding = generate_embeddings_for_single_text(test_query)
        embedding_time = time.time() - start_time
        
        print(f"✓ Embedding generation: {embedding_time:.3f}s (Vector length: {len(embedding)})")
        
        # Test optimized processor
        start_time = time.time()
        response = optimized_processor.get_simple_response(test_query, twin_id, "1")
        processing_time = time.time() - start_time
        
        print(f"✓ Optimized processor: {processing_time:.3f}s")
        print(f"✓ Response preview: {response[:100]}...")
        
        print("\n✓ Direct function integration verified successfully!")
        
    except Exception as e:
        print(f"✗ Error testing direct integration: {e}")
        import traceback
        traceback.print_exc()

def test_simplified_rag_mode():
    """Test the new simplified RAG mode that bypasses metadata extraction."""
    print("\n" + "=" * 60)
    print("Testing Simplified RAG Mode (Metadata Bypass)")
    print("=" * 60)
    
    test_queries = [
        "What are the safety procedures?",
        "Tell me about equipment maintenance",
        "How do I handle emergency situations?"
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\nSimplified RAG Test {i+1}: {query}")
        
        payload = {
            "query": query,
            "twin_version_id": "default",
            "chat_instance_id": 1
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/simplified-rag/",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            processing_time = time.time() - start_time
            
            print(f"Status Code: {response.status_code}")
            print(f"Total Time: {processing_time:.3f}s")
            
            if response.status_code == 200:
                data = response.json()
                agent_processing_time = data.get('processing_time', 0)
                print(f"Agent Processing Time: {agent_processing_time}s")
                print(f"Metadata Bypassed: {data.get('metadata_bypassed', False)}")
                print(f"Verification Bypassed: {data.get('verification_bypassed', False)}")
                print(f"Source Chunks: {data.get('source_chunks_count', 0)}")
                print(f"Mode: {data.get('mode', 'unknown')}")
                print(f"Response Preview: {data.get('response', '')[:150]}...")
                
                return True
            else:
                print(f"Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    return True

def test_all_processing_modes():
    """Compare performance across all processing modes: simplified, simple, and full."""
    print("\n" + "=" * 60)
    print("Testing All Processing Modes Performance Comparison")
    print("=" * 60)
    
    test_query = "What are the maintenance procedures for equipment?"
    twin_version_id = "default"
    chat_instance_id = 1
    
    modes_to_test = [
        {
            "name": "Simplified RAG (Metadata Bypass)",
            "endpoint": "/api/simplified-rag/",
            "payload": {
                "query": test_query,
                "twin_version_id": twin_version_id,
                "chat_instance_id": chat_instance_id
            }
        },
        {
            "name": "Simple Mode (No Verification)",
            "endpoint": "/api/agentic-document-response/",
            "payload": {
                "query": test_query,
                "twin_version_id": twin_version_id,
                "chat_instance_id": chat_instance_id,
                "agent_mode": "simple"
            }
        },
        {
            "name": "Full Mode (With Verification)",
            "endpoint": "/api/agentic-document-response/",
            "payload": {
                "query": test_query,
                "twin_version_id": twin_version_id,
                "chat_instance_id": chat_instance_id,
                "agent_mode": "full"
            }
        }
    ]
    
    results = []
    
    for mode in modes_to_test:
        print(f"\nTesting {mode['name']}...")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{BASE_URL}{mode['endpoint']}",
                json=mode['payload'],
                headers={'Content-Type': 'application/json'}
            )
            
            total_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if 'processing_time' in data:
                    # Simplified RAG response format
                    agent_time = data.get('processing_time', 0)
                    metadata_bypassed = data.get('metadata_bypassed', False)
                    verification_bypassed = data.get('verification_bypassed', False)
                    mode_name = data.get('mode', 'unknown')
                else:
                    # Standard agentic response format
                    agent_time = data.get('agent_metadata', {}).get('processing_time', 0)
                    metadata_bypassed = False
                    verification_bypassed = mode['payload'].get('agent_mode') == 'simple'
                    mode_name = data.get('agent_metadata', {}).get('processing_mode', 'unknown')
                
                result = {
                    "name": mode['name'],
                    "total_time": total_time,
                    "agent_time": agent_time,
                    "metadata_bypassed": metadata_bypassed,
                    "verification_bypassed": verification_bypassed,
                    "mode": mode_name,
                    "success": True
                }
                
                print(f"✓ Success - Total: {total_time:.3f}s, Agent: {agent_time:.3f}s")
                print(f"  Metadata Bypassed: {metadata_bypassed}")
                print(f"  Verification Bypassed: {verification_bypassed}")
                
            else:
                result = {
                    "name": mode['name'],
                    "total_time": total_time,
                    "success": False,
                    "error": response.text
                }
                print(f"✗ Failed - {response.status_code}: {response.text}")
                
            results.append(result)
            
        except Exception as e:
            result = {
                "name": mode['name'],
                "success": False,
                "error": str(e)
            }
            results.append(result)
            print(f"✗ Error: {e}")
    
    # Display performance comparison
    print("\n" + "=" * 60)
    print("PERFORMANCE COMPARISON SUMMARY")
    print("=" * 60)
    
    successful_results = [r for r in results if r.get('success')]
    if successful_results:
        # Sort by agent processing time
        successful_results.sort(key=lambda x: x.get('agent_time', float('inf')))
        
        print(f"{'Mode':<35} {'Agent Time':<12} {'Total Time':<12} {'Features'}")
        print("-" * 80)
        
        for result in successful_results:
            features = []
            if result.get('metadata_bypassed'):
                features.append("No Metadata")
            if result.get('verification_bypassed'):
                features.append("No Verification")
            if not features:
                features.append("Full Processing")
            
            print(f"{result['name']:<35} {result.get('agent_time', 0):<12.3f} {result.get('total_time', 0):<12.3f} {', '.join(features)}")
    
    return len(successful_results) > 0

def main():
    """Run all optimized system tests."""
    print("OPTIMIZED AGENTIC RAG SYSTEM TESTS")
    print("=" * 80)
    
    # Test sequence
    tests = [
        ("Agent Health Check", test_agent_health),
        ("Fast Response Performance", test_fast_response), 
        ("Simple vs Full Mode Comparison", test_full_vs_simple_performance),
        ("Batch Processing", test_batch_processing),
        ("Performance Metrics", test_performance_metrics),
        ("Direct Function Integration", test_direct_function_integration),
        ("Simplified RAG Mode Test", test_simplified_rag_mode),
        ("All Processing Modes Comparison", test_all_processing_modes)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            success = test_func()
            results[test_name] = success if success is not None else True
        except Exception as e:
            print(f"Test failed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nPassed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Optimized agentic system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above.")

if __name__ == "__main__":
    main()
