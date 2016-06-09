import React from 'react';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';

import {actions as changeActions} from '../change-reducers';


class ChangeDetail extends React.Component {
  render() {
    const {change} = this.props;
    return (
      <div>
        <h1>{change.event} {change.resource_name} {change.resource_id}</h1>
        Change detail for id: {change.id}
      </div>
    );
  }
}

@connect(
  state => ({
    change: state.changes.item || {},
  }),
  dispatch => ({
    actions: bindActionCreators({...changeActions}, dispatch)
  })
)
class ChangeDetailContainer extends React.Component {
  componentDidMount() {
    const {changeId} = this.props.params;
    const {actions} = this.props;
    actions.getChange(changeId);
  }

  render() {
    const {change} = this.props;
    return (
      <ChangeDetail change={change} />
    );
  }
}

export default ChangeDetailContainer;
