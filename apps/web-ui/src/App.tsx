import React from 'react';
import { ConfigProvider, Layout, Menu, theme } from 'antd';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import {
  DashboardOutlined,
  DatabaseOutlined,
  ThunderboltOutlined,
  BarChartOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import CrudOperations from './pages/CrudOperations';
import LoadTesting from './pages/LoadTesting';
import Monitoring from './pages/Monitoring';
import Settings from './pages/Settings';

const { Header, Sider, Content } = Layout;

const App: React.FC = () => {
  const [collapsed, setCollapsed] = React.useState(false);
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
      }}
    >
      <Router>
        <Layout style={{ minHeight: '100vh' }}>
          <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
            <div style={{ height: 32, margin: 16, background: 'rgba(255, 255, 255, 0.2)', borderRadius: 6 }}>
              <h3 style={{ color: 'white', textAlign: 'center', margin: '4px 0' }}>
                {collapsed ? 'CP' : 'Cassandra Perf'}
              </h3>
            </div>
            <Menu theme="dark" defaultSelectedKeys={['1']} mode="inline">
              <Menu.Item key="1" icon={<DashboardOutlined />}>
                <Link to="/">Dashboard</Link>
              </Menu.Item>
              <Menu.Item key="2" icon={<DatabaseOutlined />}>
                <Link to="/crud">CRUD Operations</Link>
              </Menu.Item>
              <Menu.Item key="3" icon={<ThunderboltOutlined />}>
                <Link to="/load-testing">Load Testing</Link>
              </Menu.Item>
              <Menu.Item key="4" icon={<BarChartOutlined />}>
                <Link to="/monitoring">Monitoring</Link>
              </Menu.Item>
              <Menu.Item key="5" icon={<SettingOutlined />}>
                <Link to="/settings">Settings</Link>
              </Menu.Item>
            </Menu>
          </Sider>
          <Layout>
            <Header style={{ padding: 0, background: colorBgContainer }}>
              <h2 style={{ margin: '0 24px' }}>Cassandra Performance Testing Framework</h2>
            </Header>
            <Content style={{ margin: '24px 16px 0' }}>
              <div style={{ padding: 24, minHeight: 360, background: colorBgContainer, borderRadius: 8 }}>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/crud" element={<CrudOperations />} />
                  <Route path="/load-testing" element={<LoadTesting />} />
                  <Route path="/monitoring" element={<Monitoring />} />
                  <Route path="/settings" element={<Settings />} />
                </Routes>
              </div>
            </Content>
          </Layout>
        </Layout>
      </Router>
    </ConfigProvider>
  );
};

export default App;