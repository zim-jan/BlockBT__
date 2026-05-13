declare module 'react-plotly.js' {
    import * as React from 'react';
    export interface PlotParams {
        data: any[];
        layout: any;
        config?: any;
        style?: any;
        useResizeHandler?: boolean;
        className?: string;
        onInitialized?: (figure: any, graphDiv: any) => void;
        onUpdate?: (figure: any, graphDiv: any) => void;
        onPurge?: (figure: any, graphDiv: any) => void;
        onError?: (err: any) => void;
        [key: string]: any;
    }
    export default class Plot extends React.Component<PlotParams> {}
}
