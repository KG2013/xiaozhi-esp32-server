package smhs.modules.sys.dao;

import org.apache.ibatis.annotations.Mapper;

import smhs.common.dao.BaseDao;
import smhs.modules.sys.entity.SysDictTypeEntity;

/**
 * 字典类型
 */
@Mapper
public interface SysDictTypeDao extends BaseDao<SysDictTypeEntity> {

}
