import React from "react";
import  './App.css'
import axios from 'axios';
import LoginScreen from './LoginScreen';

class App extends React.Component{
    constructor(props){
        super(props);
        this.state={
            loginPage:[],
            uploadScreen:[],
            advice:''
        }
    }

    componentDidMount() {
        console.log("Componet did mount")
        this.fetchAdvice()
        let loginPage = [];
        loginPage.push(<LoginScreen appContext={this} key={"login-screen"}/>);
        this.setState({
            loginPage:loginPage
        })
    }

    componentWillMount(){

    }

    fetchAdvice = () => {
        axios.get('\thttps://api.adviceslip.com/advice')
            .then((response)=>{
                const advice = response.data.slip;

                this.setState(advice);
            })
            .catch((error)=>{
                console.log(error)
            });

    }

    render() {
        const {advice} = this.state
        return (
            <div className="app">
                <div className="card">
                    {this.state.loginPage}
                    {this.state.uploadScreen}
                    <h1 className="header">{advice}</h1>
                    <button className="button" onClick={this.fetchAdvice}>
                        <span>Give me Advice!</span>
                    </button>
                </div>
            </div>
        );
    }
}

export default App

// import React, { Component } from 'react';
// import './App.css';
// import LoginScreen from './Loginscreen';
// class App extends Component {
//     constructor(props){
//         super(props);
//         this.state={
//             loginPage:[],
//             uploadScreen:[]
//         }
//     }
//     componentWillMount(){
//         let loginPage =[];
//         loginPage.push(<LoginScreen appContext={this} key={"login-screen"}/>);
//         this.setState({
//             loginPage:loginPage
//         })
//     }
//     render() {
//         return (

//         );
//     }
// }
//
// export default App;
