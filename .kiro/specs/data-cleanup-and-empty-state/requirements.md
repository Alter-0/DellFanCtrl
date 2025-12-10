# Requirements Document

## Introduction

本功能为 iDRAC 风扇控制器应用添加两项优化：自动数据清理和空数据状态提示。当前系统的 MonitorHistory 表会无限增长，长期运行会导致数据库膨胀和查询性能下降。同时，当历史数据为空时，前端图表显示空白，缺乏用户友好的提示。

## Glossary

- **MonitorHistory**: 存储 CPU 温度、风扇转速、功耗等监控数据的数据库表
- **DataCleanupService**: 负责定期清理过期历史数据的后台服务
- **RetentionPeriod**: 数据保留周期，超过此周期的数据将被自动删除
- **EmptyState**: 当数据为空时显示的友好提示界面组件

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want historical monitoring data to be automatically cleaned up after a configurable retention period, so that the database does not grow indefinitely and system performance remains stable.

#### Acceptance Criteria

1. WHEN the system starts THEN the DataCleanupService SHALL schedule periodic cleanup tasks based on the configured retention period
2. WHEN a cleanup task executes THEN the DataCleanupService SHALL delete all MonitorHistory records older than the retention period
3. WHEN the retention period setting is updated THEN the DataCleanupService SHALL apply the new retention period to subsequent cleanup operations
4. WHERE the retention period is configurable THEN the system SHALL provide options of 7 days, 30 days, 90 days, and 365 days with a default of 30 days
5. WHEN a cleanup operation completes THEN the DataCleanupService SHALL log the number of deleted records

### Requirement 2

**User Story:** As a user, I want to see a friendly message when there is no historical data available, so that I understand the system state and know what to expect.

#### Acceptance Criteria

1. WHEN the Dashboard component loads and the history data array is empty THEN the system SHALL display an empty state message instead of a blank chart
2. WHEN displaying the empty state THEN the system SHALL show an appropriate icon and descriptive text explaining that no data is available yet
3. WHEN new monitoring data becomes available THEN the system SHALL automatically replace the empty state with the populated chart
4. WHEN the history API returns an empty data array THEN the Dashboard component SHALL detect this condition and render the empty state component
