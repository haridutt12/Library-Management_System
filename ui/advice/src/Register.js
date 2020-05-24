import React, { Component } from 'react';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';
import AppBar from 'material-ui/AppBar';
import RaisedButton from 'material-ui/RaisedButton';
import TextField from 'material-ui/TextField';
import DropDownMenu from 'material-ui/DropDownMenu';
import MenuItem from 'material-ui/MenuItem';
import axios from 'axios';
import Login from "./Login";

class Register extends Component {
    constructor(props) {
        super(props);
        this.state = {
            first_name: '',
            last_name: '',
            email: '',
            username: '',
            role: '',
        }
    }

    render() {
        return (
            <div>
                <MuiThemeProvider>
                    <div>
                        <AppBar
                            title="Register"
                        />
                        <TextField
                            hintText="Enter your First Name"
                            floatingLabelText="First Name"
                            onChange={(event, newValue) => this.setState({first_name: newValue})}
                        />
                        <br/>
                        <TextField
                            hintText="Enter your Last Name"
                            floatingLabelText="Last Name"
                            onChange={(event, newValue) => this.setState({last_name: newValue})}
                        />
                        <br/>
                        <TextField
                            hintText="Enter your Email"
                            type="email"
                            floatingLabelText="Email"
                            onChange={(event, newValue) => this.setState({email: newValue})}
                        />
                        <br/>
                        <TextField
                            hintText="Enter your Username"
                            floatingLabelText="Username"
                            onChange={(event, newValue) => this.setState({username: newValue})}
                        />
                        <br/>
                        <div>
                            <p>Login as:</p>
                            <DropDownMenu value={this.state.role}
                                          onChange={(event, index, value) => this.handleMenuChange(value)}>
                                <MenuItem value={1} primaryText="Student"/>
                                <MenuItem value={2} primaryText="Teacher"/>
                            </DropDownMenu>
                        </div>
                        <br/>
                        <RaisedButton label="Submit" primary={true} style={style}
                                      onClick={(event) => this.handleClick(event)}/>
                    </div>
                </MuiThemeProvider>
            </div>
        );
    }

    handleClick(event) {
        let apiBaseUrl = "http://localhost:5000/";
        console.log("values", this.state.first_name, this.state.last_name, this.state.email, this.state.password);
        //To be done:check for empty values before hitting submit
        let self = this;
        let payload = {
            "fname": this.state.first_name,
            "lname": this.state.last_name,
            "email": this.state.email,
            "username": this.state.password,
            "role": this.state.role
        }
        axios.post(apiBaseUrl + '/users', payload)
            .then(function (response) {
                console.log(response);
                if (response.data.code === 200) {
                    //  console.log("registration successful");
                    let loginscreen = [];
                    self.loginscreen.push(<Login parentContext={this}/>);
                    let loginmessage = "Not Registered yet.Go to registration";
                    self.props.parentContext.setState({
                        loginscreen: loginscreen,
                        loginmessage: loginmessage,
                        buttonLabel: "Register",
                        isLogin: true
                    });
                }
            })
            .catch(function (error) {
                console.log(error);
            });
    }
}

const style = {
    margin: 15,
};

export default Register;
