package smhs.modules.sys.dao;

import org.apache.ibatis.annotations.Mapper;

import smhs.common.dao.BaseDao;
import smhs.modules.sys.entity.SysUserEntity;

/**
 * 系统用户
 */
@Mapper
public interface SysUserDao extends BaseDao<SysUserEntity> {

}