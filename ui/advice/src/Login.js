import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';
import AppBar from 'material-ui/AppBar';
import RaisedButton from 'material-ui/RaisedButton';
import TextField from 'material-ui/TextField';
import React, {Component} from "react";
import axios from 'axios';
import  createMuiTheme  from '@material-ui/core/styles/createMuiTheme';
import {Mui} from './pallet';
import getMuiTheme from 'material-ui/styles/getMuiTheme';

// const theme = createMuiTheme({
//     pallet
// });
// const muiTheme = getMuiTheme({
//     palette: {
//         primary: ,
//
//     },
// });

class Login extends Component{

    constructor(props) {
        super(props);
        this.state = {
            username: '',
            password: ''
        }
    }

        render() {
            return (
                <div>
                    <MuiThemeProvider>
                        <div >
                            <AppBar
                                title="Login"
                            />
                            <TextField
                                hintText="Enter your Username"
                                floatingLabelText="Username"
                                onChange = {(event,newValue) => this.setState({username:newValue})}
                            />
                            <TextField
                                hintText="Enter your Password"
                                type= "password"
                                floatingLabelText="Password"
                                onChange = {(event, newValue)=> this.setState({password:newValue})}
                            />
                            <br/>
                            <RaisedButton label="Submit" primary={true} style={style} onClick={(event) => this.handleClick(event)}/>
                        </div>
                    </MuiThemeProvider>
                </div>
            );
        }
    handleClick(event){
        let apiBaseUrl = "http://localhost:5000/";
        let self = this;
        let payload={
            "email":this.state.username,
            "password":this.state.password
        }
        axios.post(apiBaseUrl+'login', payload)
            .then(function (response) {
                console.log(response);
                if(response.data.code === 200){
                    console.log("Login successful");
                    let uploadScreen=[];
                    self.uploadScreen.push(<uploadScreen appContext={self.props.appContext}/>)
                    self.props.appContext.setState({loginPage:[],uploadScreen:uploadScreen})
                }
                else if(response.data.code === 204){
                    console.log("Username password do not match");
                    alert("username password do not match")
                }
                else{
                    console.log("Username does not exists");
                    alert("Username does not exist");
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
    export default Login;







