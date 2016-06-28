import React from 'react';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';

import Paper from 'material-ui/Paper';

import {actions as attributeActions} from '../attribute-reducers';

const style = {
  margin: '16px 32px',
  padding: '16px'
}

class AttributeDetail extends React.Component {
  render() {
    const {attribute} = this.props;
    return (
      <Paper style={style}>
        <h1>{attribute.resource_name}:{attribute.name}</h1>
        <pre>{JSON.stringify(attribute, null, 4)}</pre>
      </Paper>
    );
  }
}

@connect(
  state => ({
    attribute: state.attributes.item || {},
  }),
  dispatch => ({
    actions: bindActionCreators({...attributeActions}, dispatch)
  })
)
class AttributeDetailContainer extends React.Component {
  componentDidMount() {
    const {attributeId} = this.props.params;
    const {actions} = this.props;
    actions.getAttribute(attributeId);
  }

  render() {
    const {attribute} = this.props;
    return (
      <AttributeDetail attribute={attribute} />
    );
  }
}

export default AttributeDetailContainer;
