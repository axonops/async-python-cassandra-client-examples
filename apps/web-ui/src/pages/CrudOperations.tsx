import React, { useState } from 'react';
import { Form, Input, Button, Table, Space, Modal, message, Tabs, Select, Card, Row, Col } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';

const { TabPane } = Tabs;
const { Option } = Select;
const { TextArea } = Input;

interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
  profile_data: any;
}

interface Document {
  id: string;
  title: string;
  content: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

const CrudOperations: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editingDocument, setEditingDocument] = useState<Document | null>(null);
  const [selectedApp, setSelectedApp] = useState<'async' | 'sync'>('async');
  const [form] = Form.useForm();
  const [docForm] = Form.useForm();

  const apiPrefix = selectedApp === 'async' ? '/api/async' : '/api/sync';

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${apiPrefix}/users`);
      setUsers(response.data);
    } catch (error) {
      message.error('Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${apiPrefix}/documents`);
      setDocuments(response.data);
    } catch (error) {
      message.error('Failed to fetch documents');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (values: any) => {
    try {
      const userData = {
        ...values,
        profile_data: JSON.parse(values.profile_data || '{}')
      };
      
      if (editingUser) {
        await axios.put(`${apiPrefix}/users/${editingUser.id}`, userData);
        message.success('User updated successfully');
      } else {
        await axios.post(`${apiPrefix}/users`, userData);
        message.success('User created successfully');
      }
      
      setModalVisible(false);
      form.resetFields();
      setEditingUser(null);
      fetchUsers();
    } catch (error) {
      message.error('Operation failed');
    }
  };

  const handleCreateDocument = async (values: any) => {
    try {
      const docData = {
        ...values,
        tags: values.tags ? values.tags.split(',').map((tag: string) => tag.trim()) : []
      };
      
      if (editingDocument) {
        await axios.put(`${apiPrefix}/documents/${editingDocument.id}`, docData);
        message.success('Document updated successfully');
      } else {
        await axios.post(`${apiPrefix}/documents`, docData);
        message.success('Document created successfully');
      }
      
      docForm.resetFields();
      setEditingDocument(null);
      fetchDocuments();
    } catch (error) {
      message.error('Operation failed');
    }
  };

  const handleDeleteUser = async (id: string) => {
    try {
      await axios.delete(`${apiPrefix}/users/${id}`);
      message.success('User deleted successfully');
      fetchUsers();
    } catch (error) {
      message.error('Failed to delete user');
    }
  };

  const userColumns = [
    {
      title: 'Username',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: User) => (
        <Space size="middle">
          <Button
            icon={<EditOutlined />}
            onClick={() => {
              setEditingUser(record);
              form.setFieldsValue({
                ...record,
                profile_data: JSON.stringify(record.profile_data)
              });
              setModalVisible(true);
            }}
          />
          <Button
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteUser(record.id)}
          />
        </Space>
      ),
    },
  ];

  const documentColumns = [
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: 'Tags',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => tags.join(', '),
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Document) => (
        <Space size="middle">
          <Button
            icon={<EditOutlined />}
            onClick={() => {
              setEditingDocument(record);
              docForm.setFieldsValue({
                ...record,
                tags: record.tags.join(', ')
              });
            }}
          />
          <Button
            danger
            icon={<DeleteOutlined />}
            onClick={() => {
              // Handle document deletion
              message.info('Document deletion not implemented yet');
            }}
          />
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <h2>CRUD Operations</h2>
        </Col>
        <Col>
          <Select value={selectedApp} onChange={setSelectedApp} style={{ width: 150 }}>
            <Option value="async">Async App</Option>
            <Option value="sync">Sync App</Option>
          </Select>
        </Col>
      </Row>

      <Tabs defaultActiveKey="1">
        <TabPane tab="Users" key="1">
          <Space style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setEditingUser(null);
                form.resetFields();
                setModalVisible(true);
              }}
            >
              Create User
            </Button>
            <Button icon={<ReloadOutlined />} onClick={fetchUsers}>
              Refresh
            </Button>
          </Space>
          
          <Table
            columns={userColumns}
            dataSource={users}
            loading={loading}
            rowKey="id"
          />

          <Modal
            title={editingUser ? 'Edit User' : 'Create User'}
            visible={modalVisible}
            onCancel={() => {
              setModalVisible(false);
              form.resetFields();
              setEditingUser(null);
            }}
            footer={null}
          >
            <Form form={form} layout="vertical" onFinish={handleCreateUser}>
              <Form.Item
                name="username"
                label="Username"
                rules={[{ required: true, message: 'Please input username!' }]}
              >
                <Input />
              </Form.Item>
              <Form.Item
                name="email"
                label="Email"
                rules={[
                  { required: true, message: 'Please input email!' },
                  { type: 'email', message: 'Invalid email format!' }
                ]}
              >
                <Input />
              </Form.Item>
              <Form.Item
                name="profile_data"
                label="Profile Data (JSON)"
                rules={[
                  {
                    validator: (_, value) => {
                      if (!value) return Promise.resolve();
                      try {
                        JSON.parse(value);
                        return Promise.resolve();
                      } catch {
                        return Promise.reject('Invalid JSON format!');
                      }
                    }
                  }
                ]}
              >
                <TextArea rows={4} placeholder='{"bio": "...", "location": "..."}' />
              </Form.Item>
              <Form.Item>
                <Space>
                  <Button type="primary" htmlType="submit">
                    {editingUser ? 'Update' : 'Create'}
                  </Button>
                  <Button onClick={() => {
                    setModalVisible(false);
                    form.resetFields();
                    setEditingUser(null);
                  }}>
                    Cancel
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Modal>
        </TabPane>

        <TabPane tab="Documents" key="2">
          <Card style={{ marginBottom: 16 }}>
            <Form form={docForm} layout="vertical" onFinish={handleCreateDocument}>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="title"
                    label="Title"
                    rules={[{ required: true, message: 'Please input title!' }]}
                  >
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="tags"
                    label="Tags (comma-separated)"
                  >
                    <Input placeholder="tag1, tag2, tag3" />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item
                name="content"
                label="Content"
                rules={[{ required: true, message: 'Please input content!' }]}
              >
                <TextArea rows={6} />
              </Form.Item>
              <Form.Item>
                <Space>
                  <Button type="primary" htmlType="submit">
                    {editingDocument ? 'Update' : 'Create'} Document
                  </Button>
                  {editingDocument && (
                    <Button onClick={() => {
                      setEditingDocument(null);
                      docForm.resetFields();
                    }}>
                      Cancel
                    </Button>
                  )}
                  <Button icon={<ReloadOutlined />} onClick={fetchDocuments}>
                    Refresh
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>

          <Table
            columns={documentColumns}
            dataSource={documents}
            loading={loading}
            rowKey="id"
          />
        </TabPane>
      </Tabs>
    </div>
  );
};

export default CrudOperations;