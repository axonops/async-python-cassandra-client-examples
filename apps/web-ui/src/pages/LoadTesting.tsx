import React, { useState } from 'react';
import { Card, Button, Select, InputNumber, Row, Col, Progress, Table, Space, Typography, Alert } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const { Title, Text } = Typography;
const { Option } = Select;

interface TestResult {
  timestamp: string;
  asyncRPS: number;
  syncRPS: number;
  asyncErrors: number;
  syncErrors: number;
  asyncP95: number;
  syncP95: number;
}

interface TestConfig {
  scenario: string;
  duration: number;
  users: number;
  rampUp: number;
}

const LoadTesting: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [testConfig, setTestConfig] = useState<TestConfig>({
    scenario: 'mixed',
    duration: 60,
    users: 50,
    rampUp: 10,
  });
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [currentStats, setCurrentStats] = useState({
    asyncRPS: 0,
    syncRPS: 0,
    asyncErrors: 0,
    syncErrors: 0,
    progress: 0,
  });

  const scenarios = [
    { value: 'read-heavy', label: 'Read Heavy (80% reads, 20% writes)' },
    { value: 'write-heavy', label: 'Write Heavy (20% reads, 80% writes)' },
    { value: 'mixed', label: 'Mixed (50% reads, 50% writes)' },
    { value: 'streaming', label: 'Streaming Test' },
    { value: 'batch', label: 'Batch Operations' },
  ];

  const startTest = () => {
    setIsRunning(true);
    setTestResults([]);
    
    // Simulate test execution
    let elapsed = 0;
    const interval = setInterval(() => {
      elapsed += 1;
      const progress = (elapsed / testConfig.duration) * 100;
      
      if (progress >= 100) {
        clearInterval(interval);
        setIsRunning(false);
        setCurrentStats(prev => ({ ...prev, progress: 100 }));
        return;
      }

      // Simulate test data
      const newResult: TestResult = {
        timestamp: new Date().toLocaleTimeString(),
        asyncRPS: Math.random() * 1000 + 500,
        syncRPS: Math.random() * 800 + 400,
        asyncErrors: Math.floor(Math.random() * 5),
        syncErrors: Math.floor(Math.random() * 8),
        asyncP95: Math.random() * 50 + 20,
        syncP95: Math.random() * 70 + 30,
      };

      setTestResults(prev => [...prev, newResult]);
      setCurrentStats({
        asyncRPS: newResult.asyncRPS,
        syncRPS: newResult.syncRPS,
        asyncErrors: newResult.asyncErrors,
        syncErrors: newResult.syncErrors,
        progress,
      });
    }, 1000);
  };

  const stopTest = () => {
    setIsRunning(false);
    // In real implementation, this would stop the actual load test
  };

  const columns = [
    {
      title: 'Metric',
      dataIndex: 'metric',
      key: 'metric',
    },
    {
      title: 'Async App',
      dataIndex: 'async',
      key: 'async',
      render: (value: number) => <Text strong>{value.toFixed(2)}</Text>,
    },
    {
      title: 'Sync App',
      dataIndex: 'sync',
      key: 'sync',
      render: (value: number) => <Text strong>{value.toFixed(2)}</Text>,
    },
    {
      title: 'Difference',
      dataIndex: 'diff',
      key: 'diff',
      render: (value: number) => (
        <Text type={value > 0 ? 'success' : 'danger'}>
          {value > 0 ? '+' : ''}{value.toFixed(2)}%
        </Text>
      ),
    },
  ];

  const summaryData = testResults.length > 0 ? [
    {
      key: '1',
      metric: 'Average RPS',
      async: testResults.reduce((sum, r) => sum + r.asyncRPS, 0) / testResults.length,
      sync: testResults.reduce((sum, r) => sum + r.syncRPS, 0) / testResults.length,
      diff: ((testResults.reduce((sum, r) => sum + r.asyncRPS, 0) / testResults.length) - 
             (testResults.reduce((sum, r) => sum + r.syncRPS, 0) / testResults.length)) / 
             (testResults.reduce((sum, r) => sum + r.syncRPS, 0) / testResults.length) * 100,
    },
    {
      key: '2',
      metric: 'Average P95 Latency (ms)',
      async: testResults.reduce((sum, r) => sum + r.asyncP95, 0) / testResults.length,
      sync: testResults.reduce((sum, r) => sum + r.syncP95, 0) / testResults.length,
      diff: ((testResults.reduce((sum, r) => sum + r.syncP95, 0) / testResults.length) - 
             (testResults.reduce((sum, r) => sum + r.asyncP95, 0) / testResults.length)) / 
             (testResults.reduce((sum, r) => sum + r.syncP95, 0) / testResults.length) * 100,
    },
    {
      key: '3',
      metric: 'Total Errors',
      async: testResults.reduce((sum, r) => sum + r.asyncErrors, 0),
      sync: testResults.reduce((sum, r) => sum + r.syncErrors, 0),
      diff: 0,
    },
  ] : [];

  return (
    <div>
      <Title level={2}>Load Testing</Title>
      
      <Alert
        message="Load Testing Information"
        description="This UI demonstrates load testing controls. In production, this would trigger actual load tests using Locust or k6. 
                     For real testing, use the command-line tools provided in the load-testing directory."
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Card title="Test Configuration">
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div>
                <Text>Scenario:</Text>
                <Select
                  value={testConfig.scenario}
                  onChange={(value) => setTestConfig({ ...testConfig, scenario: value })}
                  style={{ width: '100%', marginTop: 8 }}
                  disabled={isRunning}
                >
                  {scenarios.map(s => (
                    <Option key={s.value} value={s.value}>{s.label}</Option>
                  ))}
                </Select>
              </div>

              <div>
                <Text>Duration (seconds):</Text>
                <InputNumber
                  min={10}
                  max={600}
                  value={testConfig.duration}
                  onChange={(value) => setTestConfig({ ...testConfig, duration: value || 60 })}
                  style={{ width: '100%', marginTop: 8 }}
                  disabled={isRunning}
                />
              </div>

              <div>
                <Text>Virtual Users:</Text>
                <InputNumber
                  min={1}
                  max={1000}
                  value={testConfig.users}
                  onChange={(value) => setTestConfig({ ...testConfig, users: value || 50 })}
                  style={{ width: '100%', marginTop: 8 }}
                  disabled={isRunning}
                />
              </div>

              <div>
                <Text>Ramp-up Period (seconds):</Text>
                <InputNumber
                  min={0}
                  max={60}
                  value={testConfig.rampUp}
                  onChange={(value) => setTestConfig({ ...testConfig, rampUp: value || 10 })}
                  style={{ width: '100%', marginTop: 8 }}
                  disabled={isRunning}
                />
              </div>

              <Space style={{ marginTop: 16, width: '100%' }}>
                {!isRunning ? (
                  <Button type="primary" icon={<PlayCircleOutlined />} onClick={startTest} block>
                    Start Test
                  </Button>
                ) : (
                  <Button danger icon={<PauseCircleOutlined />} onClick={stopTest} block>
                    Stop Test
                  </Button>
                )}
              </Space>
            </Space>
          </Card>
        </Col>

        <Col span={16}>
          <Card title="Test Progress" style={{ marginBottom: 16 }}>
            <Progress percent={currentStats.progress} status={isRunning ? 'active' : undefined} />
            <Row gutter={16} style={{ marginTop: 16 }}>
              <Col span={6}>
                <Statistic title="Async RPS" value={currentStats.asyncRPS.toFixed(0)} />
              </Col>
              <Col span={6}>
                <Statistic title="Sync RPS" value={currentStats.syncRPS.toFixed(0)} />
              </Col>
              <Col span={6}>
                <Statistic title="Async Errors" value={currentStats.asyncErrors} />
              </Col>
              <Col span={6}>
                <Statistic title="Sync Errors" value={currentStats.syncErrors} />
              </Col>
            </Row>
          </Card>

          <Card title="Real-time Metrics">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={testResults.slice(-30)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="asyncRPS" stroke="#1890ff" name="Async RPS" />
                <Line type="monotone" dataKey="syncRPS" stroke="#ff7875" name="Sync RPS" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {testResults.length > 0 && (
        <Card title="Test Summary" style={{ marginTop: 16 }}>
          <Table columns={columns} dataSource={summaryData} pagination={false} />
        </Card>
      )}
    </div>
  );
};

// Add missing import
import { Statistic } from 'antd';

export default LoadTesting;