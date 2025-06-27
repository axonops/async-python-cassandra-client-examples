import React from 'react';
import { Card, Tabs, Alert, Button, Space } from 'antd';
import { ExportOutlined, ReloadOutlined } from '@ant-design/icons';

const { TabPane } = Tabs;

const Monitoring: React.FC = () => {
  const grafanaUrl = process.env.GRAFANA_URL || 'http://localhost:3000';
  
  const dashboards = [
    {
      key: 'comparison',
      title: 'Performance Comparison',
      uid: 'async-sync-comparison',
      description: 'Side-by-side comparison of async vs sync application performance'
    },
    {
      key: 'cassandra',
      title: 'Cassandra Operations',
      uid: 'cassandra-operations',
      description: 'Detailed Cassandra query performance and operation metrics'
    },
    {
      key: 'resources',
      title: 'System Resources',
      uid: 'system-resources',
      description: 'CPU, memory, and system resource utilization'
    }
  ];

  const openGrafana = (dashboardUid?: string) => {
    const url = dashboardUid 
      ? `${grafanaUrl}/d/${dashboardUid}`
      : grafanaUrl;
    window.open(url, '_blank');
  };

  return (
    <div>
      <h2>Monitoring</h2>
      
      <Alert
        message="Grafana Integration"
        description="Click on any dashboard below to open it in Grafana. Default credentials: admin/admin"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
        action={
          <Button size="small" onClick={() => openGrafana()}>
            Open Grafana <ExportOutlined />
          </Button>
        }
      />

      <Tabs defaultActiveKey="comparison">
        {dashboards.map(dashboard => (
          <TabPane tab={dashboard.title} key={dashboard.key}>
            <Card>
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <h3>{dashboard.title}</h3>
                  <p>{dashboard.description}</p>
                </div>
                
                <Space>
                  <Button 
                    type="primary" 
                    icon={<ExportOutlined />}
                    onClick={() => openGrafana(dashboard.uid)}
                  >
                    Open in Grafana
                  </Button>
                  <Button icon={<ReloadOutlined />}>
                    Refresh
                  </Button>
                </Space>

                <div style={{ 
                  height: 600, 
                  border: '1px solid #d9d9d9', 
                  borderRadius: 4,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: '#f5f5f5'
                }}>
                  <Space direction="vertical" align="center">
                    <p>Grafana dashboard would be embedded here in production</p>
                    <Button onClick={() => openGrafana(dashboard.uid)}>
                      Open Dashboard <ExportOutlined />
                    </Button>
                  </Space>
                </div>
              </Space>
            </Card>
          </TabPane>
        ))}
      </Tabs>

      <Card title="Quick Links" style={{ marginTop: 24 }}>
        <Space wrap>
          <Button onClick={() => window.open('http://localhost:9090', '_blank')}>
            Prometheus UI <ExportOutlined />
          </Button>
          <Button onClick={() => window.open('http://localhost:3000', '_blank')}>
            Grafana <ExportOutlined />
          </Button>
          <Button onClick={() => window.open('http://localhost:8001/docs', '_blank')}>
            Async API Docs <ExportOutlined />
          </Button>
          <Button onClick={() => window.open('http://localhost:8002/docs', '_blank')}>
            Sync API Docs <ExportOutlined />
          </Button>
        </Space>
      </Card>
    </div>
  );
};

export default Monitoring;