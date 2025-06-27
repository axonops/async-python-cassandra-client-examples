import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Badge, Space, Select, Typography, Spin } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const { Title } = Typography;
const { Option } = Select;

interface HealthStatus {
  status: string;
  cassandra: string;
  app_type: string;
}

interface MetricData {
  time: string;
  asyncRPS: number;
  syncRPS: number;
  asyncP95: number;
  syncP95: number;
}

const Dashboard: React.FC = () => {
  const [asyncHealth, setAsyncHealth] = useState<HealthStatus | null>(null);
  const [syncHealth, setSyncHealth] = useState<HealthStatus | null>(null);
  const [metricData, setMetricData] = useState<MetricData[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);

  const fetchHealth = async () => {
    try {
      const [asyncRes, syncRes] = await Promise.all([
        axios.get('/api/async/health'),
        axios.get('/api/sync/health')
      ]);
      setAsyncHealth(asyncRes.data);
      setSyncHealth(syncRes.data);
    } catch (error) {
      console.error('Error fetching health:', error);
    }
  };

  const fetchMetrics = async () => {
    try {
      // Simulate metrics data - in real app, this would come from Prometheus
      const now = new Date();
      const newDataPoint: MetricData = {
        time: now.toLocaleTimeString(),
        asyncRPS: Math.random() * 1000 + 500,
        syncRPS: Math.random() * 800 + 400,
        asyncP95: Math.random() * 50 + 20,
        syncP95: Math.random() * 70 + 30,
      };
      
      setMetricData(prev => {
        const updated = [...prev, newDataPoint];
        return updated.slice(-20); // Keep last 20 data points
      });
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      await Promise.all([fetchHealth(), fetchMetrics()]);
      setLoading(false);
    };

    fetchData();
    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'degraded':
        return <ClockCircleOutlined style={{ color: '#faad14' }} />;
      default:
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
    }
  };

  if (loading && metricData.length === 0) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  const latestMetrics = metricData[metricData.length - 1] || {
    asyncRPS: 0,
    syncRPS: 0,
    asyncP95: 0,
    syncP95: 0,
  };

  const improvement = ((latestMetrics.asyncRPS - latestMetrics.syncRPS) / latestMetrics.syncRPS * 100).toFixed(1);

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>Performance Dashboard</Title>
        </Col>
        <Col>
          <Space>
            <span>Refresh Interval:</span>
            <Select value={refreshInterval} onChange={setRefreshInterval} style={{ width: 120 }}>
              <Option value={1000}>1 second</Option>
              <Option value={5000}>5 seconds</Option>
              <Option value={10000}>10 seconds</Option>
              <Option value={30000}>30 seconds</Option>
            </Select>
          </Space>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Async App Status"
              value={asyncHealth?.status || 'Unknown'}
              prefix={asyncHealth && getHealthIcon(asyncHealth.status)}
              valueStyle={{ color: asyncHealth?.status === 'healthy' ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Sync App Status"
              value={syncHealth?.status || 'Unknown'}
              prefix={syncHealth && getHealthIcon(syncHealth.status)}
              valueStyle={{ color: syncHealth?.status === 'healthy' ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Performance Improvement"
              value={improvement}
              suffix="%"
              valueStyle={{ color: parseFloat(improvement) > 0 ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Cassandra Status"
              value="Connected"
              prefix={<Badge status="success" />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col span={12}>
          <Card title="Requests Per Second">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metricData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="asyncRPS" stroke="#1890ff" name="Async" />
                <Line type="monotone" dataKey="syncRPS" stroke="#ff7875" name="Sync" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="P95 Response Time (ms)">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metricData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="asyncP95" stroke="#1890ff" name="Async P95" />
                <Line type="monotone" dataKey="syncP95" stroke="#ff7875" name="Sync P95" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col span={24}>
          <Card title="Current Performance Metrics">
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Statistic 
                  title="Async RPS" 
                  value={latestMetrics.asyncRPS.toFixed(2)} 
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col span={6}>
                <Statistic 
                  title="Sync RPS" 
                  value={latestMetrics.syncRPS.toFixed(2)} 
                  valueStyle={{ color: '#ff7875' }}
                />
              </Col>
              <Col span={6}>
                <Statistic 
                  title="Async P95 Latency" 
                  value={latestMetrics.asyncP95.toFixed(2)} 
                  suffix="ms"
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col span={6}>
                <Statistic 
                  title="Sync P95 Latency" 
                  value={latestMetrics.syncP95.toFixed(2)} 
                  suffix="ms"
                  valueStyle={{ color: '#ff7875' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;