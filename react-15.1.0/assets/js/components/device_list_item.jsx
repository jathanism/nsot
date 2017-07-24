import React from 'react'

class DeviceListItem extends React.Component {

  render() {
    return (
      <div className="list-group-item">
        <div className="pull-right">
          <button
            className="btn btn-default"
            onClick={this.props.onClickEdit(this.props.device.id)}>Edit</button>
        </div>
        <h4 className="list-group-item-heding">{this.props.device.hostname}</h4>
        <div className="list-group-item-text">
          {JSON.stringify(this.props.device.attributes)}
        </div>
      </div>

    )
  }

}

module.exports = DeviceListItem;
