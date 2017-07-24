import React from 'react'
import {RestForm, Forms} from 'react-at-rest'

class DeviceForm extends RestForm {

  render() {
    let deleteButton;
    let cancelButton;

    // Only show delete/cancel button if the resource already exists in the DB
    // (e.g. Update vs. Create)
    if (this.props.model.id) {
      deleteButton = <button className='btn btn-danger' onClick={this.handleDestroy}>Delete</button>;
      cancelButton = <button className='btn btn-default' onClick={this.props.handleEditComplete}>Cancel</button>;
    }

    // Build the form for a device
    return (
      <div className="list-group-item">
        <form onSubmit={this.handleSubmit}>
          <Forms.TextInput {...this.getFieldProps('hostname')} autoFocus={true} />
          <div className='text-right'>
            {cancelButton}
            &nbsp;
            {deleteButton}
            &nbsp;
            <button className='btn btn-primary' disabled={_.isEmpty(this.state.patch)}>Save</button>
          </div>
        </form>
      </div>
    )
  }

}

module.exports = DeviceForm;
