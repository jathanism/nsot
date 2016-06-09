import React from 'react';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';

import {actions as attributeActions} from '../attribute-reducers';


class AttributeDetail extends React.Component {
  render() {
    const {attribute} = this.props;
    return (
      <div>
        <h1>{attribute.resource_name}:{attribute.name}</h1>
        Attribute detail for id: {attribute.id}
      </div>
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
