<template>
  <div class="welcome">
    <HeaderBar />

    <div class="operation-bar">
      <h2 class="page-title">{{ $t('device.management') }}</h2>
      <div class="right-operations">
        <el-input :placeholder="$t('device.searchPlaceholder')" v-model="searchKeyword" class="search-input"
          @keyup.enter.native="handleSearch" clearable />
        <el-button class="btn-search" @click="handleSearch">{{ $t('device.search') }}</el-button>
      </div>
    </div>

    <div class="main-wrapper">
      <div class="content-panel">
        <div class="content-area">
          <el-card class="device-card" shadow="never">
            <el-table ref="deviceTable" :data="paginatedDeviceList" class="transparent-table"
              :header-cell-class-name="headerCellClassName" v-loading="loading"
              :element-loading-text="$t('deviceManagement.loading')" element-loading-spinner="el-icon-loading"
              element-loading-background="rgba(255, 255, 255, 0.7)">
              <el-table-column :label="$t('modelConfig.select')" align="center" width="120">
                <template slot-scope="scope">
                  <el-checkbox v-model="scope.row.selected"></el-checkbox>
                </template>
              </el-table-column>
              <!-- <el-table-column :label="$t('device.model')" prop="model" align="center">
                <template slot-scope="scope">
                  {{ getFirmwareTypeName(scope.row.model) }}
                </template>
              </el-table-column> -->
              <!-- <el-table-column :label="$t('device.roleName')" prop=""
                align="center"></el-table-column> -->
              <el-table-column :label="$t('device.deviceCode')" prop="ssid"
                align="center"></el-table-column>
              <el-table-column :label="$t('device.deviceBrand')" prop="deviceBrand"
                align="center"></el-table-column>
              <el-table-column :label="$t('device.deviceChannel')" prop="deviceChannel"
              align="center"></el-table-column>
              <el-table-column :label="$t('device.deviceSeries')" prop="deviceSeries"
              align="center"></el-table-column>
              <el-table-column :label="$t('device.deviceType')" prop="deviceType"
              align="center"></el-table-column>
              <el-table-column :label="$t('device.deviceModel')" prop="deviceModel"
              align="center"></el-table-column>
              <el-table-column :label="$t('device.deviceStatus')" prop="deviceStatusName"
              align="center"></el-table-column>
              <el-table-column :label="$t('device.deviceRemarks')" prop="remark"
              align="center"></el-table-column>
              <el-table-column :label="$t('device.deviceCreateTime')" prop="createDate"
              align="center"></el-table-column>
              <el-table-column :label="$t('device.deviceUpdateTime')" prop="updateDate"
              align="center"></el-table-column>

              <!-- <el-table-column :label="$t('device.macAddress')" prop="macAddress" align="center"></el-table-column>
              <el-table-column :label="$t('device.bindTime')" prop="bindTime" align="center"></el-table-column>
              <el-table-column :label="$t('device.lastConversation')" prop="lastConversation"
                align="center"></el-table-column>
              <el-table-column v-if="mqttServiceAvailable" :label="$t('device.deviceStatus')" prop="deviceStatus" align="center">
                <template slot-scope="scope">
                  <el-tag v-if="scope.row.deviceStatus === 'online'" type="success">{{ $t('device.online') }}</el-tag>
                  <el-tag v-else type="danger">{{ $t('device.offline') }}</el-tag>
                </template>
              </el-table-column> -->
              <!-- <el-table-column :label="$t('device.remark')" align="center">
                <template #default="{ row }">
                  <el-input v-show="row.isEdit" v-model="row.remark" size="mini" maxlength="64" show-word-limit
                    @blur="onRemarkBlur(row)" @keyup.enter.native="onRemarkEnter(row)" />
                  <span v-show="!row.isEdit" class="remark-view">
                    <i class="el-icon-edit" @click="row.isEdit = true" style="cursor: pointer;"></i>
                    <span @click="row.isEdit = true">
                      {{ row.remark || '-' }}
                    </span>
                  </span>
                </template>
              </el-table-column> -->
              <!-- <el-table-column :label="$t('device.autoUpdate')" align="center">
                <template slot-scope="scope">
                  <el-switch v-model="scope.row.otaSwitch" size="mini" active-color="#13ce66" inactive-color="#ff4949"
                    @change="handleOtaSwitchChange(scope.row)"></el-switch>
                </template>
              </el-table-column> -->

              <el-table-column :label="$t('device.operation')" align="center">
                <template slot-scope="scope">
                  <el-button size="mini" type="text" @click="deviceView(scope.row.ssid)">
                    {{ $t('device.view') }}
                  </el-button>
                  <el-button size="mini" type="text" @click="handleEnable(scope.row)">
                    {{scope.row.deviceStatus==1 ? '开启' : '禁用'}}
                  </el-button>
                  <el-button size="mini" type="text" @click="deviceDelete(scope.row.ssid)">
                    {{ $t('device.isdelete') }}
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <div class="table_bottom">
              <div class="ctrl_btn">
                <el-button size="mini" type="primary" class="select-all-btn" @click="handleSelectAll">
                  {{ isCurrentPageAllSelected ? $t('common.deselectAll') : $t('common.selectAll') }}
                </el-button>
                <el-button type="success" size="mini" class="add-device-btn" @click="deviceAdd()" >
                  {{ $t('device.deviceAdd') }}
                </el-button>
                <el-button type="success" size="mini" class="add-device-btn" @click="batchDeleteDevice()" >
                  批量删除 
                </el-button>
                <el-button type="success" size="mini" class="add-device-btn" @click="handleBatchEnable(true)" >
                  批量启用 
                </el-button>
                <el-button type="success" size="mini" class="add-device-btn" @click="handleBatchEnable(false)" >
                  批量禁用 
                </el-button>
                <!-- <el-button type="success" size="mini" class="add-device-btn" @click="handleAddDevice">
                  {{ $t('device.bindWithCode') }}
                </el-button> -->
                <!-- <el-button type="success" size="mini" class="add-device-btn" @click="handleManualAddDevice">
                  {{ $t('device.manualAdd') }}
                </el-button> -->
                <!-- <el-button size="mini" type="danger" icon="el-icon-delete" @click="deleteSelected">
                  {{ $t('device.unbind') }}
                </el-button> -->
              </div>
              <div class="custom-pagination">
                <el-select v-model="pageSize" @change="handlePageSizeChange" class="page-size-select">
                  <el-option v-for="item in pageSizeOptions" :key="item" 
                    :label="$t('dictManagement.itemsPerPage').replace('{items}', item)" :value="item">
                  </el-option>
                </el-select>
                <button class="pagination-btn" :disabled="currentPage === 1" @click="goFirst">
                  {{ $t('dictManagement.firstPage') }}
                </button>
                <button class="pagination-btn" :disabled="currentPage === 1" @click="goPrev">
                  {{ $t('dictManagement.prevPage') }}
                </button>
                <button v-for="page in visiblePages" :key="page" class="pagination-btn"
                  :class="{ active: page === currentPage }" @click="goToPage(page)">
                  {{ page }}
                </button>
                <button class="pagination-btn" :disabled="currentPage === pageCount" @click="goNext">
                  {{ $t('dictManagement.nextPage') }}
                </button>
                <span class="total-text">
                  共{{ deviceList.length }}条记录
                </span>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </div>

    <el-dialog :title="dialogTitle" :visible.sync="dialogFormVisible" width="50%">
      <el-collapse v-model="activeNames" @change="handleChange">
        <el-collapse-item title="设备基础信息" name="1" >
          <div style="padding: 0 20px;">
            <el-form :model="ruleForm" :rules="rules" ref="ruleForm" label-width="80px" class="demo-ruleForm">
              <div class="item">
                <!-- <el-form-item label="角色" prop="roleName">
                  <el-select v-model="ruleForm.roleName" size="small" clearable filterable placeholder="请选择角色">
                    <el-option
                      v-for="item in options"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value">
                    </el-option>
                  </el-select>
                </el-form-item> -->
                <el-form-item label="品牌" prop="deviceBrand">
                  <el-select :disabled="isViewMode" v-model="ruleForm.deviceBrand" size="small" clearable filterable placeholder="请选择品牌">
                    <el-option
                      v-for="item in dictDeviceBrand"
                      :key="item.key"
                      :label="item.name"
                      :value="item.key">
                    </el-option>
                  </el-select>
                </el-form-item>
                <el-form-item label="渠道" prop="deviceChannel">
                  <el-select :disabled="isViewMode" v-model="ruleForm.deviceChannel" size="small" clearable filterable placeholder="请选择渠道">
                    <el-option
                      v-for="item in dictDeviceChannel"
                      :key="item.key"
                      :label="item.name"
                      :value="item.key">
                    </el-option>
                  </el-select>
                </el-form-item>
              </div>
              <div class="item">
                <el-form-item label="系列" prop="deviceSeries">
                  <el-select :disabled="isViewMode" v-model="ruleForm.deviceSeries" size="small" clearable filterable placeholder="请选择系列">
                    <el-option
                      v-for="item in dictDeviceSeries"
                      :key="item.key"
                      :label="item.name"
                      :value="item.key">
                    </el-option>
                  </el-select>
                </el-form-item>
                <el-form-item label="设备类型" prop="deviceType">
                  <!-- <div style="display: flex; align-items: center;height:40px">
                    <el-radio v-model="ruleForm.deviceType" label="1">正式</el-radio>
                    <el-radio v-model="ruleForm.deviceType" label="2">非正式</el-radio>
                  </div> -->
                  <el-radio-group :disabled="isViewMode" v-model="ruleForm.deviceType">
                    <el-radio 
                      v-for="item in dictDeviceType"
                      :key="item.key"
                      :label="item.name"
                      :value="item.key"
                      >
                    </el-radio>
                  </el-radio-group>
                </el-form-item>
              </div>
              <div class="item">
                <el-form-item label="型号" prop="deviceModel">
                  <el-select :disabled="isViewMode" v-model="ruleForm.deviceModel" size="small" clearable filterable placeholder="请选择型号">
                    <el-option
                      v-for="item in dictDeviceModel"
                      :key="item.key"
                      :label="item.name"
                      :value="item.key">
                    </el-option>
                  </el-select>
                </el-form-item>
                <el-form-item label="备注信息">
                  <el-input
                    class="el-input"
                    maxlength="20"
                    size="small"
                    placeholder="请输入备注信息"
                    v-model="ruleForm.remark"
                    :disabled="isViewMode"
                    clearable>
                  </el-input>
                </el-form-item>
              </div>
              <div class="item">
                <el-form-item label="批量数量">
                  <el-input-number :disabled="isViewMode" class="el-input-number" v-model="deviceBatchNum" size="small" controls-position="right" @change="handleChange" :min="0" :max="100"></el-input-number>
                </el-form-item>
              </div>
            </el-form>
          </div>
          <el-row v-if="!isViewMode">
            <el-button size="small" type="primary" :disabled="isViewMode|| (ruleForm.hardwareCode && ruleForm.hardwareCode.length > 0)" @click="generateHardwareCode('ruleForm')">生成硬件编码</el-button>
            <el-button size="small" type="primary" :disabled="isViewMode|| (ruleForm.hardwareCode && ruleForm.hardwareCode.length > 0)" @click="batchGenerateHardwareCode('ruleForm')">批量生成硬件编码</el-button>
            <div style="color:red;margin-top:10px;font-size:14px">注:只有设备基础信息全部录入成功才可以生成硬件编码;批量生成须填写批量数量</div>
          </el-row>
        </el-collapse-item>
        <el-collapse-item title="硬件编码信息" name="2">
          <div class="item hardware-code-container">
            <span>硬件编码:</span>
            <div class="hardware-code-list">
              <div v-for="(item, index) in ruleForm.hardwareCode" :key="index" class="hardware-code-item">
                <el-input
                  class="hardware-code-input"
                  size="small"
                  v-model="ruleForm.hardwareCode[index]"
                  :disabled="true">
                </el-input>
              </div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
      <div slot="footer" class="dialog-footer" v-if="!isViewMode">
        <el-button @click="dialogFormVisible = false">取 消</el-button>
        <el-button type="primary" @click="submitDeviceForm('ruleForm')">确 定</el-button>
      </div>
    </el-dialog>

    <!-- <AddDeviceDialog :visible.sync="addDeviceDialogVisible" :agent-id="currentAgentId"
      @refresh="fetchBindDevices(currentAgentId)" />
    <ManualAddDeviceDialog :visible.sync="manualAddDeviceDialogVisible" :agent-id="currentAgentId"
      @refresh="fetchBindDevices(currentAgentId)" /> -->

  </div>
</template>

<script>
import Api from '@/apis/api';
import AddDeviceDialog from "@/components/AddDeviceDialog.vue";
import HeaderBar from "@/components/HeaderBar.vue";
import ManualAddDeviceDialog from "@/components/ManualAddDeviceDialog.vue";

export default {
  components: {
    HeaderBar,
    AddDeviceDialog,
    ManualAddDeviceDialog
  },
  data() {
    return {
      addDeviceDialogVisible: false,
      manualAddDeviceDialogVisible: false,
      selectedDeviceId: '',
      searchKeyword: "",
      activeSearchKeyword: "",
      currentAgentId: this.$route.query.agentId || '',
      currentPage: 1,
      pageSize: 10,
      pageSizeOptions: [10, 20, 50, 100],
      deviceList: [],
      total:0,
      loading: false,
      userApi: null,
      firmwareTypes: [],
      dialogFormVisible:false,
      activeNames: ['1'],
      dictDeviceBrand: [],
      dictDeviceChannel: [],
      dictDeviceModel: [],
      dictDeviceSeries: [],
      dictDeviceType:[],
      ruleForm:{
        // roleName:'',  //角色
        ssid:'', //设备ssid
        deviceBrand:'',  //品牌
        deviceChannel:'',  //渠道
        deviceSeries:'',  //系列
        deviceType:'',  // 设备类型
        deviceModel:'',  //型号
        deviceStatus:'', //状态
        deviceStatusName:'', //中文状态  已启用、已禁用
        remark:'',  //备注信息
        hardwareCode: []  //硬件编码：改为数组，统一处理单个或批量返回
      },
      ssids: [], // 存储生成的所有硬件编码
      deviceBatchNum: 0,
      isViewMode:false,
      rules:{
        // roleName:[
        //   {required: true, message: '请选择角色', trigger: 'change'}
        // ],
        deviceBrand:[
          {required: true, message: '请选择品牌', trigger: 'change'}
        ],
        deviceChannel:[
          {required: true, message: '请选择渠道', trigger: 'change'}
        ],
        deviceSeries:[
          {required: true, message: '请选择系列', trigger: 'change'}
        ],
        deviceType:[
          {required: true, message: '请至少选择一个设备类型', trigger: 'change'}
        ],
        deviceModel:[
          {required: true, message: '请选择型号', trigger: 'change'}
        ]
      },
      mqttServiceAvailable: false, // MQTT服务是否可用
    };
  },
  computed: {
    // pageCount() {
    //   return Math.ceil(this.filteredDeviceList.length / this.pageSize);
    // },
    dialogTitle(){
      return this.isViewMode ?'查看设备':'添加设备';
    },
    pageCount() {
      return Math.ceil((Number(this.total) || 0) / this.pageSize);
    },
     visiblePages() {
      const pages = [];
      const maxVisible = 3;
      let start = Math.max(1, this.currentPage - 1);
      let end = Math.min(this.pageCount, start + maxVisible - 1);

      if (end - start + 1 < maxVisible) {
        start = Math.max(1, end - maxVisible + 1);
      }

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
      return pages;
    },
    filteredDeviceList() {
      const keyword = (this.activeSearchKeyword || '').toLowerCase();
      if (!keyword) return this.deviceList;
      // 根据 fetchParams 返回的字段调整搜索字段：ssid / deviceModel / deviceBrand
      return this.deviceList.filter(device =>
        (device.ssid && String(device.ssid).toLowerCase().includes(keyword)) ||
        (device.deviceModel && String(device.deviceModel).toLowerCase().includes(keyword)) ||
        (device.deviceBrand && String(device.deviceBrand).toLowerCase().includes(keyword))
      );
    },

    paginatedDeviceList() {
      return this.filteredDeviceList;
    },
    
    // 计算当前页是否全选
    isCurrentPageAllSelected() {
      return this.paginatedDeviceList.length > 0 &&
        this.paginatedDeviceList.every(device => device.selected);
    },
  },
  mounted() {
    const agentId = this.$route.query.agentId;
    // if (agentId) {
    //   this.fetchBindDevices(agentId);
    // }
    this.fetchParams();
  },
  created() {
    this.getFirmwareTypes()
    this.getDeviceBrand()
    this.getDeviceChannel()
    this.getDeviceModel()
    this.getDeviceSeries()
    this.getDeviceType()
  },
  methods: {
    async getDeviceBrand() {
      try {
        const res = await Api.dict.getDictDataByType('device_brand')
        this.dictDeviceBrand = res.data
      } catch (error) {
        this.$message.error(error.message || '获取品牌字典数据失败')
      }
    },
    async getDeviceChannel() {
      try {
        const res = await Api.dict.getDictDataByType('device_channel')
        this.dictDeviceChannel = res.data
      } catch (error) {
        this.$message.error(error.message || '获取渠道字典数据失败')
      }
    },
    async getDeviceModel() {
      try {
        const res = await Api.dict.getDictDataByType('device_model')
        this.dictDeviceModel = res.data
      } catch (error) {
        this.$message.error(error.message || '获取型号字典数据失败')
      }
    },
    async getDeviceSeries() {
      try {
        const res = await Api.dict.getDictDataByType('device_series')
        this.dictDeviceSeries = res.data
      } catch (error) {
        this.$message.error(error.message || '获取系列字典数据失败')
      }
    },
    async getDeviceType() {
      try {
        const res = await Api.dict.getDictDataByType('device_type')
        this.dictDeviceType = res.data
      } catch (error) {
        this.$message.error(error.message || '获取类型字典数据失败')
      }
    },
    async getFirmwareTypes() {
      try {
        const res = await Api.dict.getDictDataByType('FIRMWARE_TYPE')
        this.firmwareTypes = res.data
      } catch (error) {
        console.error(this.$t('device.getFirmwareTypeFailed') + ':', error)
        this.$message.error(error.message || this.$t('device.getFirmwareTypeFailed'))
      }
    },
    // 批量开启、禁用
    handleBatchEnable(bool){
      const selectedSsids = this.paginatedDeviceList
				.filter(d => d.selected)
				.map(d => d.ssid)
				.filter(Boolean);
      console.log('selectedSsids',selectedSsids)
			if (selectedSsids.length === 0) {
				this.$message.warning({
					message: '请至少选择一条记录',
					showClose: true
				});
				return;
			}
      let str = `enable=${bool}`
      str += `&ssids=${String(selectedSsids)}`
      Api.device.devicebatchEnable(str,({data})=>{
        if(data.code ===0){
          this.$message({
            message: bool ? '启用成功' : '禁用成功',
            type: 'success'
          });
          this.fetchParams(this.page)
        }else{
          this.$message.error({
							message: (data && data.msg)|| bool ? '启用失败':'禁用失败',
							showClose: true
					});
          this.fetchParams(this.page)
        }
      })
    },
    // 启用禁用切换
    handleEnable(row){
      let enable = row.deviceStatus == 0? false:true
      let str = `enable=${enable = row.deviceStatus == 0? false:true}`
      str += `&ssids=${String(row.ssid)}`
      Api.device.devicebatchEnable(str,({data})=>{
        if(data.code ===0){
          this.$message({
            message: enable ? '启用成功' : '禁用成功',
            type: 'success'
          });
          this.fetchParams(this.page)
        }else{
          this.$message.error({
							message: (data && data.msg) || enable ? '启用成功' : '禁用成功',
							showClose: true
					});
          this.fetchParams(this.page)
        }
      })
    },
    // 生成单个硬件编码
    generateHardwareCode(formName) {
      if (this.ruleForm.hardwareCode && this.ruleForm.hardwareCode.length > 0) {
        this.$message.info('已生成硬件编码，无法重复生成')
        return
      }
      this.$refs[formName].validate((valid) => {
        if (valid) {
          const selectedLabel = this.ruleForm.deviceType;
          let mappedKeys = [];
          if (Array.isArray(selectedLabel)) {
            mappedKeys = selectedLabel.map(l => {
              const f = this.dictDeviceType.find(d => d.name === l);
              return f ? f.key : null;
            }).filter(Boolean);
          } else {
            const f = this.dictDeviceType.find(d => d.name === selectedLabel);
            if (f) mappedKeys = [f.key];
          }
          if (mappedKeys.length) {
            this.ruleForm.deviceType = mappedKeys[0];
          }
          const agentId = this.currentAgentId
          const deviceBatchNum = this.deviceBatchNum
          const params ={...this.ruleForm,agentId,deviceBatchNum}
          Api.device.getDeviceCode(params,({data})=>{
            if(data.code === 0){
              const codes = Array.isArray(data.data) ? data.data : [data.data];
              this.ruleForm.hardwareCode = codes;
              this.ssids = codes;
              this.$message.success('硬件编码生成成功')
            }else{
              this.$message.error('生成设备编码失败')
            }
          })
        }else{
          this.$message.error('请填写设备的基础信息')
          return
        }
      });
    },
    // 批量生成硬件编码
    batchGenerateHardwareCode(formName) {
      if (this.ruleForm.hardwareCode && this.ruleForm.hardwareCode.length > 0) {
        this.$message.info('已生成硬件编码，无法重复生成')
        return
      }
      this.$refs[formName].validate((valid) => {
        if (valid) {
          if (this.deviceBatchNum <= 0 || this.deviceBatchNum > 100) {
            this.$message.warning('请输入有效的批量数量（1-100）')
            return
          }
          const selectedLabel = this.ruleForm.deviceType;
          let mappedKeys = [];
          if (Array.isArray(selectedLabel)) {
            mappedKeys = selectedLabel.map(l => {
              const f = this.dictDeviceType.find(d => d.name === l);
              return f ? f.key : null;
            }).filter(Boolean);
          } else {
            const f = this.dictDeviceType.find(d => d.name === selectedLabel);
            if (f) mappedKeys = [f.key];
          }
          if (mappedKeys.length) {
            this.ruleForm.deviceType = mappedKeys[0];
          }
          const agentId = this.currentAgentId
          const deviceBatchNum = this.deviceBatchNum
          const params ={...this.ruleForm,agentId,deviceBatchNum}
          Api.device.getBatchDeviceCode(params,({data})=>{
            if(data.code === 0){
              const codes = Array.isArray(data.data) ? data.data : [data.data];
              this.ruleForm.hardwareCode = codes;
              this.ssids = codes;
               this.$message.success('批量生成硬件编码成功')
            }else{
              this.$message.error('批量生成设备编码失败')
            }
          })
        }else{
          this.$message.error('请填写设备的基础信息')
          return
        }
      });
    },
    // 提交设备表单
    submitDeviceForm(formName) {
      if (this.isViewMode) {
        this.dialogFormVisible = false
        return
      }
      this.$refs[formName].validate((valid) => {
        if (valid) {
          if (!this.ruleForm.hardwareCode || this.ruleForm.hardwareCode.length === 0) {
            this.$message.warning('请先生成硬件编码')
            return
          }
          const agentId = this.currentAgentId
          const deviceBatchNum = this.deviceBatchNum
          const ssids = this.ssids
          const params ={...this.ruleForm,agentId,deviceBatchNum,ssids}
          Api.device.addBindDevice(params,({data})=>{
            if(data.code === 0){
              this.$message.success('设备添加成功')
              this.dialogFormVisible = false
              this.fetchParams()
            }else{
              this.$message.error('设备添加失败')
            }
          })
        }else{
          this.$message.error('请填写设备的基础信息')
          return
        }
      });
    },
    deviceDelete(ssids) {
      this.$confirm('是否确认删除此数据?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        const params = Array.isArray(ssids)?ssids:[ssids]
        Api.device.newDeleteDevice(params,({data})=>{
          if(data.code ===0){
            this.$message({
            type: 'success',
            message: '删除成功!'
            });
            this.fetchParams()
          }
        })
        
      }).catch(() => {
        this.$message({
          type: 'info',
          message: '已取消删除'
        });          
      });
    },
    deviceView(ssid){
      const params = String(ssid)
      Api.device.getDeviceDetail(params,({data})=>{
        if(data.code ===0){
          this.ruleForm = data.data
          this.ruleForm.hardwareCode = [data.data.ssid]
          this.ruleForm.deviceType = data.data.deviceTypeName
          this.isViewMode = true
          this.dialogFormVisible = true
        }else{
          this.$message.error('获取详情失败')
        }
      })
    },
    deviceAdd(){
      this.isViewMode = false
      this.dialogFormVisible = true
      // 重置表单数据
      this.ruleForm = {
        roleName:'',
        deviceBrand:'',
        deviceChannel:'',
        deviceSeries:'',
        deviceType:null,
        deviceModel:'',
        deviceStatusName:'',
        remark:'',
        hardwareCode: []
      }
      this.ssids = []
      this.deviceBatchNum=0
       // 清除上次的校验提示（避免打开对话框时立即显示必填错误）
      this.$nextTick(() => {
        if (this.$refs.ruleForm && this.$refs.ruleForm.clearValidate) {
          this.$refs.ruleForm.clearValidate();
        }
      });
    },
    handlePageSizeChange(val) {
      this.pageSize = val;
      this.currentPage = 1;
      this.fetchParams()
    },
    fetchParams(){
      this.loading = true;
      const agentId = this.currentAgentId;
      Api.device.getNewListData(
        {
            page: this.currentPage,
            limit: this.pageSize,
            agentId:agentId
        },
        ({ data }) => {
          this.loading = false;
          console.log('列表',data)
          if (data.code === 0) {
              this.deviceList = data.data.list.map(device => ({
                  createDate:device.createDate,
                  updateDate:device.updateDate,
                  deviceBrand:device.deviceBrandName,
                  deviceChannel:device.deviceChannelName,
                  deviceSeries:device.deviceSeriesName,
                  deviceType:device.deviceTypeName,
                  deviceModel:device.deviceModelName,
                  deviceStatusName:device.deviceStatusName,
                  deviceStatus:device.deviceStatus,
                  remark:device.remark||'无',
                  ssid:device.ssid,
                  selected: false,
                  showValue: false
              }));
              this.total = data.data.total;
          } else {
              this.$message.error({
                  message: data.msg,
                  showClose: true
              });
          }
        }
      );
    },
    // fetchBindDevices(agentId) {
    //   this.loading = true;
    //   Api.device.getAgentBindDevices(agentId, ({ data }) => {
    //     this.loading = false;
    //     console.log('data',data)
    //     if (data.code === 0) {
    //       this.deviceList = data.data.map(device => {
    //         return {
    //           device_id: device.id,
    //           model: device.board,
    //           firmwareVersion: device.appVersion,
    //           macAddress: device.macAddress,
    //           bindTime: device.createDate,
    //           lastConversation: device.lastConnectedAt,
    //           remark: device.alias,
    //           _originalRemark: device.alias,
    //           isEdit: false,
    //           _submitting: false,
    //           otaSwitch: device.autoUpdate === 1,
    //           rawBindTime: new Date(device.createDate).getTime(),
    //           selected: false,
    //           // 初始设置为离线状态
    //           deviceStatus: 'offline',
    //           createDate:device.createDate,
    //           updateDate:device.updateDate,
    //           deviceBrand:device.deviceBrand,
    //           deviceChannel:device.deviceChannel,
    //           deviceSeries:device.deviceSeries,
    //           deviceType:device.deviceType,
    //           deviceModel:device.deviceModel,
    //           ssid:device.ssid
    //         };
    //       })
    //         // .sort((a, b) => a.rawBindTime - b.rawBindTime);
    //       this.activeSearchKeyword = "";
    //       this.searchKeyword = "";

    //       // 获取设备列表后，立即获取设备状态
    //       this.fetchDeviceStatus(agentId);
    //     } else {
    //       this.$message.error(data.msg || this.$t('device.getListFailed'));
    //     }
    //   });
    // },
    handleSearch() {
      this.activeSearchKeyword = this.searchKeyword;
      this.currentPage = 1;
    },

    handleSelectAll() {
      const shouldSelectAll = !this.isCurrentPageAllSelected;
      this.paginatedDeviceList.forEach(row => {
        row.selected = shouldSelectAll;
      });
    },

    deleteSelected() {
      const selectedDevices = this.paginatedDeviceList.filter(device => device.selected);
      if (selectedDevices.length === 0) {
        this.$message.warning({
          message: this.$t('device.selectAtLeastOne'),
          showClose: true
        });
        return;
      }
      this.$confirm(this.$t('device.confirmBatchUnbind').replace('{count}', selectedDevices.length), this.$t('message.warning'), {
        confirmButtonText: this.$t('button.ok'),
        cancelButtonText: this.$t('button.cancel'),
        type: 'warning'
      }).then(() => {
        const deviceIds = selectedDevices.map(device => device.device_id);
        this.batchUnbindDevices(deviceIds);
      });
    },
    batchUnbindDevices(deviceIds) {
      const promises = deviceIds.map(id => {
        return new Promise((resolve, reject) => {
          Api.device.unbindDevice(id, ({ data }) => {
            if (data.code === 0) {
              resolve();
            } else {
              reject(data.msg || this.$t('device.bindFailed'));
            }
          });
        });
      });
      Promise.all(promises)
        .then(() => {
          this.$message.success({
            message: this.$t('device.batchUnbindSuccess').replace('{count}', deviceIds.length),
            showClose: true
          });
          // this.fetchBindDevices(this.currentAgentId);
        })
        .catch(error => {
          this.$message.error({
            message: error || this.$t('device.batchUnbindError'),
            showClose: true
          });
        });
    },
    handleAddDevice() {
      this.addDeviceDialogVisible = true;
    },
    handleManualAddDevice() {
      this.manualAddDeviceDialogVisible = true;
    },
    submitRemark(row) {
      if (row._submitting) return;
      const text = (row.remark || '').trim();
      if (text.length > 64) {
        this.$message.warning(this.$t('device.remarkTooLong'));
        return;
      }
      if (text === row._originalRemark) {
        return;
      }
      row._submitting = true;
      this.updateDeviceInfo(row.device_id, { alias: text }, (ok, resp) => {
        if (ok) {
          row._originalRemark = text;
          this.$message.success(this.$t('device.remarkSaved'));
        } else {
          row.remark = row._originalRemark;
          this.$message.error(resp.msg || this.$t('device.remarkSaveFailed'));
        }
        row._submitting = false;
      });
    },
    // 备注输入框：失焦时提交
    onRemarkBlur(row) {
      row.isEdit = false;
      setTimeout(() => {
        this.submitRemark(row);
      }, 100); // 延迟 100ms，避开 enter+blur 同时触发的窗口
    },
    // 备注输入框：按回车时提交
    onRemarkEnter(row) {
      row.isEdit = false;
      this.submitRemark(row);
    },
    handleUnbind(device_id) {
      this.$confirm(this.$t('device.confirmUnbind'), this.$t('message.warning'), {
        confirmButtonText: this.$t('button.ok'),
        cancelButtonText: this.$t('button.cancel'),
        type: 'warning'
      }).then(() => {
        Api.device.unbindDevice(device_id, ({ data }) => {
          if (data.code === 0) {
            this.$message.success({
              message: this.$t('device.unbindSuccess'),
              showClose: true
            });
            // this.fetchBindDevices(this.$route.query.agentId);
          } else {
            this.$message.error({
              message: data.msg || this.$t('device.unbindFailed'),
              showClose: true
            });
          }
        });
      });
    },
    goToPage(page) {
        if (page !== this.currentPage) {
            this.currentPage = page;
            this.fetchParams();
        }
    },
    goFirst() {
        if (this.currentPage !== 1) {
            this.currentPage = 1;
            this.fetchParams();
        }
    },
    goPrev() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.fetchParams();
        }
    },
    goNext() {
        if (this.currentPage < this.pageCount) {
            this.currentPage++;
            this.fetchParams();
        }
    },

    // 获取设备状态
    fetchDeviceStatus(agentId) {
      Api.device.getDeviceStatus(agentId, ({ data }) => {
        if (data.code === 0) {
          try {
            // 解析后端返回的设备状态JSON
            const statusData = JSON.parse(data.data);

            // 直接使用解析后的数据作为设备状态映射（不需要devices字段包装）
            if (statusData && typeof statusData === 'object') {
              // 成功获取到设备状态
              this.mqttServiceAvailable = true;
              // 更新设备状态
              this.updateDeviceStatusFromResponse(statusData);
            } else {
              // 数据格式不正确，MQTT服务不可用
              this.mqttServiceAvailable = false;
            }
          } catch (error) {
            // JSON解析失败，MQTT服务不可用
            this.mqttServiceAvailable = false;
          }
        } else {
          // 接口调用失败，MQTT服务不可用
          this.mqttServiceAvailable = false;
        }
      });
    },

    // 根据API响应更新设备状态
    updateDeviceStatusFromResponse(deviceStatusMap) {
      this.deviceList.forEach(device => {
        // 构建设备的MQTT客户端ID
        const macAddress = device.macAddress ? device.macAddress.replace(/:/g, '_') : 'unknown';
        const groupId = device.model ? device.model.replace(/:/g, '_') : 'GID_default';
        const mqttClientId = `${groupId}@@@${macAddress}@@@${macAddress}`;

        // 从状态映射中获取设备状态
        if (deviceStatusMap[mqttClientId]) {
          const statusInfo = deviceStatusMap[mqttClientId];

          let isOnline = false;
          if (statusInfo.isAlive === true) {
            isOnline = true;
          } else if (statusInfo.isAlive === false) {
            isOnline = false;
          } else if (statusInfo.isAlive === null && statusInfo.exists === true) {
            isOnline = true;
          } else {
            isOnline = false;
          }

          device.deviceStatus = isOnline ? 'online' : 'offline';
        } else {
          // 如果没有找到对应的状态信息，默认为离线
          device.deviceStatus = 'offline';
        }
      });
    },
    headerCellClassName({ columnIndex }) {
      if (columnIndex === 0) {
        return "custom-selection-header";
      }
      return "";
    },
    getFirmwareTypeName(type) {
      const firmwareType = this.firmwareTypes.find(item => item.key === type)
      return firmwareType ? firmwareType.name : type
    },
    updateDeviceInfo(device_id, payload, callback) {
      return Api.device.updateDeviceInfo(device_id, payload, ({ data }) => {
        callback(data.code === 0, data);
      })
    },
    handleOtaSwitchChange(row) {
      this.updateDeviceInfo(row.device_id, { autoUpdate: row.otaSwitch ? 1 : 0 }, (result, { msg }) => {
        if (result) {
          this.$message.success(row.otaSwitch ? this.$t('device.autoUpdateEnabled') : this.$t('device.autoUpdateDisabled'));
          return;
        }
        row.otaSwitch = !row.otaSwitch
        this.$message.error(msg || this.$t('message.error'))
      })
    },
    // 批量删除：收集选中行的 ssid，调用同一删除接口
		batchDeleteDevice() {
			const selectedSsids = this.paginatedDeviceList
				.filter(d => d.selected)
				.map(d => d.ssid)
				.filter(Boolean);
			if (selectedSsids.length === 0) {
				this.$message.warning({
					message: this.$t('device.selectAtLeastOne') || '请至少选择一条记录',
					showClose: true
				});
				return;
			}
			this.$confirm(`确定要删除选中的 ${selectedSsids.length} 条设备吗？`, this.$t('message.warning') || '提示', {
				confirmButtonText: this.$t('button.ok') || '确定',
				cancelButtonText: this.$t('button.cancel') || '取消',
				type: 'warning'
			}).then(() => {
				Api.device.newDeleteDevice(selectedSsids, ({ data }) => {
					if (data && data.code === 0) {
						this.$message.success({
							message: '删除成功',
							showClose: true
						});
						// 刷新当前页数据
						this.fetchParams();
					} else {
						this.$message.error({
							message: (data && data.msg) || '删除失败',
							showClose: true
						});
					}
				}, (err) => {
					this.$message.error({
						message: (err && err.message) || '删除失败',
						showClose: true
					});
				});
			}).catch(() => {
				this.$message.info({
					message: '已取消删除',
					showClose: true
				});
			});
		},
  }
};
</script>

<style scoped>

/deep/ .cell{
  padding-left: 0px!important;
  padding-right: 0px!important;
}
/deep/ .el-form-item__content{
  text-align: left;
}
/deep/ .el-dialog__header{
  text-align-last: left;
  padding-bottom: 0px!important;
}
/deep/ .el-collapse-item__header{
  font-size: 17px;
}
.el-input{
  /* width: 50%!important; */
  margin-bottom: 10px
}
.welcome {
  min-width: 900px;
  min-height: 506px;
  height: 100vh;
  display: flex;
  position: relative;
  flex-direction: column;
  background: linear-gradient(to bottom right, #dce8ff, #e4eeff, #e6cbfd);
  background-size: cover;
  -webkit-background-size: cover;
  -o-background-size: cover;
}

.main-wrapper {
  margin: 5px 22px;
  border-radius: 15px;
  min-height: calc(100vh - 24vh);
  height: auto;
  max-height: 80vh;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  position: relative;
  background: rgba(237, 242, 255, 0.5);
  display: flex;
  flex-direction: column;
}

.operation-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
}

.page-title {
  font-size: 24px;
  margin: 0;
  color: #2c3e50;
}

.right-operations {
  display: flex;
  gap: 10px;
  margin-left: auto;
}

.search-input {
  width: 280px!important;
  border-radius: 4px;
}

.btn-search {
  background: linear-gradient(135deg, #6b8cff, #a966ff);
  border: none;
  color: white;
  height: 40px;
}

::v-deep .search-input .el-input__inner {
  border-radius: 4px;
  border: 1px solid #DCDFE6;
  background-color: white;
  transition: border-color 0.2s;
}

::v-deep .page-size-select {
  width: 100px!important;
  margin-right: 8px;
}

::v-deep .page-size-select .el-input__inner {
  height: 32px;
  line-height: 32px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  background: #dee7ff;
  color: #606266;
  font-size: 14px;
}

::v-deep .page-size-select .el-input__suffix {
  right: 6px;
  width: 15px;
  height: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  top: 6px;
  border-radius: 4px;
}

::v-deep .page-size-select .el-input__suffix-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

::v-deep .page-size-select .el-icon-arrow-up:before {
  content: "";
  display: inline-block;
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 9px solid #606266;
  position: relative;
  transform: rotate(0deg);
  transition: transform 0.3s;
}

::v-deep .search-input .el-input__inner:focus {
  border-color: #6b8cff;
  outline: none;
}

.content-panel {
  flex: 1;
  display: flex;
  overflow: hidden;
  height: 100%;
  border-radius: 15px;
  background: transparent;
  border: 1px solid #fff;
}

.content-area {
  flex: 1;
  height: 100%;
  min-width: 600px;
  overflow: auto;
  background-color: white;
  display: flex;
  flex-direction: column;
}

.device-card {
  background: white;
  border: none;
  box-shadow: none;
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

::v-deep .el-card__body {
  padding: 15px;
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.table_bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  padding-bottom: 10px;
}


.ctrl_btn {
  display: flex;
  gap: 8px;
  padding-left: 26px;
}

.ctrl_btn .el-button {
  min-width: 72px;
  height: 32px;
  padding: 7px 12px 7px 10px;
  font-size: 12px;
  border-radius: 4px;
  line-height: 1;
  font-weight: 500;
  border: none;
  transition: all 0.3s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.ctrl_btn .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.ctrl_btn .el-button--primary {
  background: #5f70f3;
  color: white;
}

.ctrl_btn .el-button--success {
  background: #5bc98c;
  color: white;
}

.ctrl_btn .el-button--danger {
  background: #fd5b63;
  color: white;
}

.custom-pagination {
  display: flex;
  align-items: center;
  gap: 10px;
}

.custom-pagination .el-select {
  margin-right: 8px;
}

.custom-pagination .pagination-btn:first-child,
.custom-pagination .pagination-btn:nth-child(2),
.custom-pagination .pagination-btn:nth-last-child(2),
.custom-pagination .pagination-btn:nth-child(3) {
  min-width: 70px;
  height: 32px;
  padding: 0 12px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  background: #dee7ff;
  color: #606266;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.custom-pagination .pagination-btn:first-child:hover,
.custom-pagination .pagination-btn:nth-child(2):hover,
.custom-pagination .pagination-btn:nth-last-child(2):hover,
.custom-pagination .pagination-btn:nth-child(3):hover {
  background: #d7dce6;
}

.custom-pagination .pagination-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.custom-pagination .pagination-btn:not(:first-child):not(:nth-child(3)):not(:nth-child(2)):not(:nth-last-child(2)) {
  min-width: 28px;
  height: 32px;
  padding: 0;
  border-radius: 4px;
  border: 1px solid transparent;
  background: transparent;
  color: #606266;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.custom-pagination .pagination-btn:not(:first-child):not(:nth-child(3)):not(:nth-child(2)):not(:nth-last-child(2)):hover {
  background: rgba(245, 247, 250, 0.3);
}

.custom-pagination .pagination-btn.active {
  background: #5f70f3 !important;
  color: #ffffff !important;
  border-color: #5f70f3 !important;
}

.custom-pagination .pagination-btn.active:hover {
  background: #6d7cf5 !important;
}

.custom-pagination .total-text {
  color: #909399;
  font-size: 14px;
  margin-left: 10px;
}
/* .total-text{
  width: 20px;
} */
:deep(.transparent-table) {
  background: white;
  border: none;
}

:deep(.transparent-table .el-table__header th) {
  background: white !important;
  color: black;
  border-right: none !important;
}

:deep(.transparent-table .el-table__body tr td) {
  border-top: 1px solid rgba(0, 0, 0, 0.04);
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  border-right: none !important;
}

:deep(.transparent-table .el-table__header tr th:first-child .cell),
:deep(.transparent-table .el-table__body tr td:first-child .cell) {
  padding-left: 10px;
}

:deep(.el-icon-edit) {
  color: #7079aa;
  cursor: pointer;
}

:deep(.el-icon-edit:hover) {
  color: #5a64b5;
}

:deep(.custom-selection-header .el-checkbox) {
  display: none !important;
}


:deep(.el-table .el-button--text) {
  color: #7079aa;
}

:deep(.el-table .el-button--text:hover) {
  color: #5a64b5;
}

:deep(.transparent-table) {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 40vh);
}

:deep(.el-table__body-wrapper) {
  flex: 1;
  overflow-y: auto;
  max-height: none !important;
}

:deep(.el-table__header-wrapper) {
  flex-shrink: 0;
}

@media (min-width: 1144px) {
  .table_bottom {
    margin-top: 40px;
  }

  :deep(.transparent-table) .el-table__body tr td {
    padding-top: 16px;
    padding-bottom: 16px;
  }
}

:deep(.el-checkbox__inner) {
  background-color: #eeeeee !important;
  border-color: #cccccc !important;
}

:deep(.el-checkbox__inner:hover) {
  border-color: #cccccc !important;
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #5f70f3 !important;
  border-color: #5f70f3 !important;
}

:deep(.el-table--border::after,
::v-deep .el-table--group::after,
::v-deep .el-table::before ){
  display: none !important;
}

/* 设备添加对话框样式优化 */
.el-dialog__body {
  padding: 20px 30px;
}

.el-collapse {
  border: none;
}

.el-collapse-item__header {
  font-size: 20px;
  font-weight: 500;
  color: #303133;
  background-color: #f5f7fa;
  padding: 0 20px;
  border-radius: 4px;
  margin-bottom: 15px;
}

.el-collapse-item__content {
  padding: 0;
  padding-bottom: 20px;
}

/* 表单项样式 */
.item {
  display: flex;
  /* align-items: center; */
  gap: 15px;
}

.item span {
  min-width: 70px;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
  text-align: right;
}

.item .span1 {
  margin-left: 0;
}

.demo-ruleForm .el-form-item {
  margin-bottom: 15px;
  display: inline-block;
  width: 48%;
  margin-right: 2%;
}

.demo-ruleForm .el-form-item:nth-child(2n) {
  margin-right: 0;
}

.demo-ruleForm .el-form-item__label {
  text-align: right;
  color: #333;
}

.demo-ruleForm .el-form-item__label:before {
  content: "*";
  color: #f56c6c;
  margin-right: 4px;
}

.demo-ruleForm .el-form-item:nth-child(7) .el-form-item__label:before,
.demo-ruleForm .el-form-item:nth-child(8) .el-form-item__label:before {
  content: "";
}

/* 选择框和输入框样式 */
.el-select,
.el-input,
.el-input-number {
  width: 100%;
  min-width: 0;
}

/* 单选框样式 */
.el-radio {
  margin-right: 20px;
}

.el-radio__label {
  font-size: 14px;
  color: #606266;
}

/* 按钮样式 */
.el-row {
  margin-top: 25px;
  text-align: center;
}

.el-row .el-button {
  margin: 0 10px;
  min-width: 140px;
  height: 36px;
  font-size: 14px;
  border-radius: 4px;
  display: inline-block;
}

/* 对话框底部按钮 */
.dialog-footer {
  text-align: center;
  padding-top: 20px;
  /* border-top: 1px solid #e4e7ed; */
}

.dialog-footer .el-button {
  min-width: 100px;
  margin: 0 10px;
  border-radius: 4px;
}

/* 硬件编码逐行显示样式（覆盖全局 .el-input 宽度 50%） */
.hardware-code-container .hardware-code-list {
  display: flex;
  flex-direction: column;
  width: 100%;
}
.hardware-code-container .hardware-code-item {
  margin-bottom: 8px;
  width: 100%;
}
/* 更具体的选择器以覆盖全局 .el-input { width:50% !important; } */
.hardware-code-container .hardware-code-input {
  width: 100% !important;
  display: block;
}
/* 内部输入框也保证占满 */
.hardware-code-container .hardware-code-input >>> .el-input__inner,
.hardware-code-container .hardware-code-input ::v-deep .el-input__inner {
  width: 100% !important;
}
</style>
