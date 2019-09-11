import QtQuick 2.0
import QtCharts 2.13

Item {
    id: root

    property ChartView chart
    property ValueAxis axisX
    property real min: axisX.min
    property real max: axisX.max
    property var channels: []
    property var channelsByCenterFreq: ({})
    property bool channelsBuilt: false

    property real freqScalar: 1 / freqRangeSize
    property real freqRangeSize: max - min
    signal geometryUpdate()
    signal rangeUpdate()


    onAxisXChanged: {
        var obj;
        if (axisX){
            for (var i=0;i<channels.length;i++){
                obj = channels[i];
                obj.axisX = axisX;
            }
        }
    }

    onXChanged: { geometryUpdate() }
    onYChanged: { geometryUpdate() }
    onWidthChanged: { geometryUpdate() }
    onHeightChanged: { geometryUpdate() }

    onMinChanged: { Qt.callLater(rangeUpdate) }
    onMaxChanged: { Qt.callLater(rangeUpdate) }
    onFreqScalarChanged: { Qt.callLater(rangeUpdate) }
    onFreqRangeSizeChanged: { Qt.callLater(rangeUpdate) }

    function buildComponent(prnt, uri, props, callback){
        var component = Qt.createComponent(uri),
            obj;
        function onComponentReady(){
            if (component.status == Component.Ready){
                obj = component.createObject(prnt, props);
                if (callable(callback)){
                    callback(obj);
                }
            } else {
                console.error('Error creating object: ', component.errorString());
            }
        }
        if (component.status == Component.Ready){
            obj = component.createObject(prnt, props);
            if (callable(callback)){
                callback(obj);
            }
        } else if (component.status == Component.Error){
            console.error('Error creating object: ', component.errorString());
        } else {
            component.statusChanged.connect(onComponentReady);
        }
    }

    function buildChannels(){
        if (root.channelsBuilt){
            return;
        }
        var channel = 14, bandwidth = 6.0, centerFreq = 473.0, props;
        while (channel <= 83){
            props = {
                'channel':channel, 'bandwidth':bandwidth, 'centerFreq':centerFreq,
                'parentChannels':root, 'axisX':root.axisX,
            };
            buildComponent(root, 'UHFChannel.qml', props, function(obj){
                root.channels.push(obj);
                root.channelsByCenterFreq[obj.centerFreq] = obj;
            });
            channel += 1;
            centerFreq += bandwidth;
            root.channelsBuilt = true;
        }
    }
    Component.onCompleted: {
        buildChannels();
    }
}
