"""性能测试配置

该模块定义了性能测试的配置参数和基准值，包括：
1. 测试场景配置
2. 负载参数配置
3. 性能指标基准
4. 测试数据配置
"""

from typing import Dict, Any

# 测试场景配置
TEST_SCENARIOS = {
    # 爬虫性能测试
    'crawler': {
        'name': '爬虫性能测试',
        'description': '测试爬虫系统在不同并发下的性能表现',
        'duration': 3600,  # 测试持续时间（秒）
        'ramp_up': 300,   # 预热时间（秒）
        'cool_down': 300, # 冷却时间（秒）
        'scenarios': {
            'light_load': {
                'name': '轻负载',
                'description': '模拟轻负载场景',
                'concurrent_users': 10,
                'spawn_rate': 1,
                'target_rps': 10
            },
            'normal_load': {
                'name': '正常负载',
                'description': '模拟正常负载场景',
                'concurrent_users': 50,
                'spawn_rate': 5,
                'target_rps': 50
            },
            'heavy_load': {
                'name': '重负载',
                'description': '模拟重负载场景',
                'concurrent_users': 100,
                'spawn_rate': 10,
                'target_rps': 100
            }
        }
    },
    
    # 处理性能测试
    'processor': {
        'name': '处理性能测试',
        'description': '测试数据处理系统的性能表现',
        'duration': 1800,
        'ramp_up': 180,
        'cool_down': 180,
        'scenarios': {
            'light_load': {
                'name': '轻负载',
                'description': '模拟轻负载场景',
                'batch_size': 100,
                'interval': 10,
                'target_tps': 10
            },
            'normal_load': {
                'name': '正常负载',
                'description': '模拟正常负载场景',
                'batch_size': 500,
                'interval': 10,
                'target_tps': 50
            },
            'heavy_load': {
                'name': '重负载',
                'description': '模拟重负载场景',
                'batch_size': 1000,
                'interval': 10,
                'target_tps': 100
            }
        }
    },
    
    # 生成性能测试
    'generator': {
        'name': '生成性能测试',
        'description': '测试内容生成系统的性能表现',
        'duration': 1800,
        'ramp_up': 180,
        'cool_down': 180,
        'scenarios': {
            'light_load': {
                'name': '轻负载',
                'description': '模拟轻负载场景',
                'concurrent_tasks': 5,
                'interval': 60,
                'target_tps': 5
            },
            'normal_load': {
                'name': '正常负载',
                'description': '模拟正常负载场景',
                'concurrent_tasks': 20,
                'interval': 60,
                'target_tps': 20
            },
            'heavy_load': {
                'name': '重负载',
                'description': '模拟重负载场景',
                'concurrent_tasks': 50,
                'interval': 60,
                'target_tps': 50
            }
        }
    }
}

# 性能指标基准
PERFORMANCE_BASELINE = {
    # 爬虫性能基准
    'crawler': {
        'response_time': {
            'p50': 500,   # 中位数响应时间（毫秒）
            'p90': 1000,  # 90分位响应时间（毫秒）
            'p95': 2000,  # 95分位响应时间（毫秒）
            'p99': 5000   # 99分位响应时间（毫秒）
        },
        'error_rate': {
            'normal': 0.01,  # 正常错误率
            'warning': 0.05, # 警告错误率
            'critical': 0.10 # 严重错误率
        },
        'throughput': {
            'light_load': 8,    # 轻负载吞吐量（请求/秒）
            'normal_load': 40,  # 正常负载吞吐量（请求/秒）
            'heavy_load': 80    # 重负载吞吐量（请求/秒）
        }
    },
    
    # 处理性能基准
    'processor': {
        'processing_time': {
            'p50': 100,   # 中位数处理时间（毫秒）
            'p90': 200,   # 90分位处理时间（毫秒）
            'p95': 500,   # 95分位处理时间（毫秒）
            'p99': 1000   # 99分位处理时间（毫秒）
        },
        'error_rate': {
            'normal': 0.001,  # 正常错误率
            'warning': 0.01,  # 警告错误率
            'critical': 0.05  # 严重错误率
        },
        'throughput': {
            'light_load': 8,    # 轻负载吞吐量（事务/秒）
            'normal_load': 40,  # 正常负载吞吐量（事务/秒）
            'heavy_load': 80    # 重负载吞吐量（事务/秒）
        }
    },
    
    # 生成性能基准
    'generator': {
        'generation_time': {
            'p50': 5000,   # 中位数生成时间（毫秒）
            'p90': 10000,  # 90分位生成时间（毫秒）
            'p95': 15000,  # 95分位生成时间（毫秒）
            'p99': 30000   # 99分位生成时间（毫秒）
        },
        'error_rate': {
            'normal': 0.01,  # 正常错误率
            'warning': 0.05, # 警告错误率
            'critical': 0.10 # 严重错误率
        },
        'throughput': {
            'light_load': 4,    # 轻负载吞吐量（生成/秒）
            'normal_load': 15,  # 正常负载吞吐量（生成/秒）
            'heavy_load': 40    # 重负载吞吐量（生成/秒）
        }
    }
}

# 系统资源基准
RESOURCE_BASELINE = {
    'cpu_usage': {
        'normal': 60,   # 正常CPU使用率（%）
        'warning': 80,  # 警告CPU使用率（%）
        'critical': 90  # 严重CPU使用率（%）
    },
    'memory_usage': {
        'normal': 70,   # 正常内存使用率（%）
        'warning': 85,  # 警告内存使用率（%）
        'critical': 95  # 严重内存使用率（%）
    },
    'disk_usage': {
        'normal': 70,   # 正常磁盘使用率（%）
        'warning': 85,  # 警告磁盘使用率（%）
        'critical': 95  # 严重磁盘使用率（%）
    }
}

# 测试数据配置
TEST_DATA = {
    # 爬虫测试数据
    'crawler': {
        'platforms': ['xhs', 'bilibili'],
        'content_types': ['article', 'video'],
        'data_size': {
            'light': 1000,    # 轻量数据集大小
            'normal': 10000,  # 正常数据集大小
            'heavy': 100000   # 重量数据集大小
        }
    },
    
    # 处理测试数据
    'processor': {
        'data_types': ['text', 'image', 'video'],
        'batch_sizes': [100, 500, 1000],
        'data_size': {
            'light': 10000,    # 轻量数据集大小
            'normal': 100000,  # 正常数据集大小
            'heavy': 1000000   # 重量数据集大小
        }
    },
    
    # 生成测试数据
    'generator': {
        'content_types': ['article', 'post', 'video'],
        'template_count': 100,
        'data_size': {
            'light': 100,    # 轻量数据集大小
            'normal': 1000,  # 正常数据集大小
            'heavy': 10000   # 重量数据集大小
        }
    }
}

def get_scenario_config(scenario: str, load_level: str = 'normal_load') -> Dict[str, Any]:
    """获取测试场景配置"""
    if scenario not in TEST_SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")
        
    config = TEST_SCENARIOS[scenario]
    if load_level not in config['scenarios']:
        raise ValueError(f"Unknown load level: {load_level}")
        
    return {
        **config,
        'current_scenario': config['scenarios'][load_level]
    }

def get_performance_baseline(component: str) -> Dict[str, Any]:
    """获取性能基准"""
    if component not in PERFORMANCE_BASELINE:
        raise ValueError(f"Unknown component: {component}")
        
    return PERFORMANCE_BASELINE[component]

def get_resource_baseline() -> Dict[str, Any]:
    """获取资源基准"""
    return RESOURCE_BASELINE

def get_test_data(component: str) -> Dict[str, Any]:
    """获取测试数据配置"""
    if component not in TEST_DATA:
        raise ValueError(f"Unknown component: {component}")
        
    return TEST_DATA[component] 