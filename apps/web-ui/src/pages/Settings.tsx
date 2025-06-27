import React, { useState } from 'react';
import { Card, Form, Input, Button, Select, InputNumber, Space, message, Divider, Typography } from 'antd';
import { SaveOutlined, ReloadOutlined } from '@ant-design/icons';

const { Option } = Select;
const { Title, Text } = Typography;

interface Settings {
  cassandraHosts: string;
  cassandraPort: number;
  cassandraKeyspace: string;
  maxConnections: number;
  connectionTimeout: number;
  requestTimeout: number;
  batchSize: number;
  logLevel: string;
}

const Settings: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const defaultSettings: Settings = {
    cassandraHosts: 'localhost',
    cassandraPort: 9042,
    cassandraKeyspace: 'perftest',
    maxConnections: 100,
    connectionTimeout: 10,
    requestTimeout: 30,
    batchSize: 100,
    logLevel: 'INFO',
  };

  const handleSave = async (values: Settings) => {
    setLoading(true);
    try {
      // In a real application, this would save to backend
      await new Promise(resolve => setTimeout(resolve, 1000));
      message.success('Settings saved successfully');
    } catch (error) {
      message.error('Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    form.setFieldsValue(defaultSettings);
    message.info('Settings reset to defaults');
  };

  return (
    <div>
      <Title level={2}>Settings</Title>
      
      <Form
        form={form}
        layout="vertical"
        initialValues={defaultSettings}
        onFinish={handleSave}
      >
        <Card title="Cassandra Configuration" style={{ marginBottom: 24 }}>
          <Form.Item
            name="cassandraHosts"
            label="Cassandra Hosts"
            tooltip="Comma-separated list of Cassandra hosts"
            rules={[{ required: true, message: 'Please input Cassandra hosts!' }]}
          >
            <Input placeholder="host1,host2,host3" />
          </Form.Item>

          <Form.Item
            name="cassandraPort"
            label="Cassandra Port"
            rules={[{ required: true, message: 'Please input Cassandra port!' }]}
          >
            <InputNumber min={1} max={65535} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="cassandraKeyspace"
            label="Keyspace"
            rules={[{ required: true, message: 'Please input keyspace!' }]}
          >
            <Input />
          </Form.Item>
        </Card>

        <Card title="Performance Configuration" style={{ marginBottom: 24 }}>
          <Form.Item
            name="maxConnections"
            label="Max Connections"
            tooltip="Maximum number of connections in the pool"
          >
            <InputNumber min={1} max={1000} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="connectionTimeout"
            label="Connection Timeout (seconds)"
            tooltip="Timeout for establishing connections"
          >
            <InputNumber min={1} max={300} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="requestTimeout"
            label="Request Timeout (seconds)"
            tooltip="Timeout for individual requests"
          >
            <InputNumber min={1} max={300} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="batchSize"
            label="Batch Size"
            tooltip="Number of operations in a batch"
          >
            <InputNumber min={1} max={5000} style={{ width: '100%' }} />
          </Form.Item>
        </Card>

        <Card title="Application Configuration" style={{ marginBottom: 24 }}>
          <Form.Item
            name="logLevel"
            label="Log Level"
          >
            <Select>
              <Option value="DEBUG">DEBUG</Option>
              <Option value="INFO">INFO</Option>
              <Option value="WARNING">WARNING</Option>
              <Option value="ERROR">ERROR</Option>
            </Select>
          </Form.Item>
        </Card>

        <Form.Item>
          <Space>
            <Button 
              type="primary" 
              htmlType="submit" 
              icon={<SaveOutlined />}
              loading={loading}
            >
              Save Settings
            </Button>
            <Button 
              icon={<ReloadOutlined />}
              onClick={handleReset}
            >
              Reset to Defaults
            </Button>
          </Space>
        </Form.Item>
      </Form>

      <Card title="Environment Information">
        <Space direction="vertical">
          <Text>
            <strong>Async API URL:</strong> {process.env.ASYNC_API_URL || 'http://localhost:8001'}
          </Text>
          <Text>
            <strong>Sync API URL:</strong> {process.env.SYNC_API_URL || 'http://localhost:8002'}
          </Text>
          <Text>
            <strong>Grafana URL:</strong> {process.env.GRAFANA_URL || 'http://localhost:3000'}
          </Text>
        </Space>
      </Card>
    </div>
  );
};

export default Settings;