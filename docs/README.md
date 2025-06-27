# Async Python Cassandra Client Performance Testing Documentation

## Table of Contents

1. [Architecture Overview](./architecture.md)
2. [Getting Started](./getting-started.md)
3. [API Reference](./api-reference.md)
4. [Load Testing Guide](./load-testing-guide.md)
5. [Performance Tuning](./performance-tuning.md)
6. [Monitoring and Dashboards](./monitoring.md)
7. [Troubleshooting](./troubleshooting.md)
8. [Advanced Testing Scenarios](./advanced-testing.md)

## Quick Links

- [Main README](../README.md)
- [CLAUDE.md - AI Assistant Instructions](../CLAUDE.md)
- [Load Testing Scripts](../load-testing/)
- [Grafana Dashboards](../monitoring/grafana/dashboards/)

## Overview

This documentation provides comprehensive guidance for using the Async Python Cassandra Client Performance Testing Framework. The framework enables thorough performance comparison between the async-cassandra client and the standard synchronous cassandra-driver.

### Key Features

- **Dual Implementation**: Identical FastAPI applications using async and sync Cassandra clients
- **Comprehensive Monitoring**: Built-in Prometheus, Grafana, and Loki integration
- **Professional Load Testing**: Pre-configured Locust and k6 test scenarios
- **Interactive Web UI**: Real-time monitoring and manual testing interface
- **Docker-based Deployment**: Single command to run the entire stack

### Use Cases

1. **Performance Benchmarking**: Compare async vs sync client performance
2. **Load Testing**: Evaluate application behavior under various load conditions
3. **Stability Testing**: Long-running tests to identify memory leaks or degradation
4. **Capacity Planning**: Determine optimal configuration for production workloads

## Documentation Structure

Each document in this guide serves a specific purpose:

- **Architecture Overview**: Understanding the system design and components
- **Getting Started**: Quick setup and first test run
- **API Reference**: Detailed endpoint documentation with examples
- **Load Testing Guide**: How to run and interpret performance tests
- **Performance Tuning**: Optimization strategies for both clients
- **Monitoring**: Understanding metrics and dashboards
- **Troubleshooting**: Common issues and solutions
- **Advanced Testing**: Complex failure scenarios and chaos testing