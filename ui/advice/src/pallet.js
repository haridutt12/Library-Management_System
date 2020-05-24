import {cyan500, lime900} from 'material-ui/styles/colors';
import getMuiTheme from 'material-ui/styles/getMuiTheme';
export const Mui = getMuiTheme({
    palette: {
        textColor: lime900
    },
    appBar: {
        height: 30,
        color: lime900,
    },

    // textFieldStyle: {
    //     color: cyan500
    // }

});
// export default {
//     myColor: {
//         main: colors.blue[500]
//     },
//     primary: {
//         contrastText: colors.green[500],
//         dark: colors.red[800],
//         main: colors.red[500],
//         light: colors.indigo[100]
//     },
//     appBar: {
//         height: 57,
//         color: colors.blue[500]
//     },
//     drawer: {
//         width: 230,
//         color: colors.blueGrey
//     },
//     raisedButton: {
//         primaryColor: colors.red,
//     }
// }
