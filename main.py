#!/usr/bin/env python


from ctrader_open_api import Client, EndPoints, Protobuf, TcpProtocol
from ctrader_open_api.endpoints import EndPoints
from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import *
from ctrader_open_api.messages.OpenApiMessages_pb2 import *
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import *
from inputimeout import TimeoutOccurred, inputimeout
from twisted.internet import reactor

if __name__ == "__main__":
    currentAccountId = 41428754
    appClientId = ""
    appClientSecret = ""
    accessToken = ""
    hostType = "Demo"
    hostType = hostType.lower()

    client = Client(
        EndPoints.PROTOBUF_LIVE_HOST
        if hostType.lower() == "live"
        else EndPoints.PROTOBUF_DEMO_HOST,
        EndPoints.PROTOBUF_PORT,
        TcpProtocol,
    )

    def connected(client):  # Callback for client connection
        print("\nConnected")
        request = ProtoOAApplicationAuthReq()
        request.clientId = appClientId
        request.clientSecret = appClientSecret
        deferred = client.send(request)
        deferred.addErrback(onError)

    def disconnected(client, reason):  # Callback for client disconnection
        print("\nDisconnected: ", reason)

    def onMessageReceived(client, message):  # Callback for receiving all messages
        if message.payloadType in [
            ProtoOASubscribeSpotsRes().payloadType,
            ProtoOAAccountLogoutRes().payloadType,
            ProtoHeartbeatEvent().payloadType,
        ]:
            return
        elif message.payloadType == ProtoOAApplicationAuthRes().payloadType:
            if currentAccountId is not None:
                sendProtoOAAccountAuthReq()
                return
        elif message.payloadType == ProtoOAAccountAuthRes().payloadType:
            protoOAAccountAuthRes = Protobuf.extract(message)
            print(
                f"Account {protoOAAccountAuthRes.ctidTraderAccountId} has been authorized\n"
            )
            print("This acccount will be used for all future requests\n")
            print("You can change the account by using setAccount command")
        else:
            print("Message received: \n", Protobuf.extract(message))
        reactor.callLater(3, callable=executeUserCommand)

    def onError(failure):  # Call back for errors
        print("Message Error: ", failure)

        reactor.callLater(3, callable=executeUserCommand)

    def setAccount(accountId):
        global currentAccountId
        if currentAccountId is not None:
            sendProtoOAAccountLogoutReq()
        currentAccountId = int(accountId)
        sendProtoOAAccountAuthReq()

    def sendProtoOAAccountLogoutReq(clientMsgId=None):
        request = ProtoOAAccountLogoutReq()
        request.ctidTraderAccountId = currentAccountId
        deferred = client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOAAccountAuthReq(clientMsgId=None):
        request = ProtoOAAccountAuthReq()
        request.ctidTraderAccountId = currentAccountId
        request.accessToken = accessToken
        deferred = client.send(request, clientMsgId=clientMsgId)
        deferred.addErrback(onError)

    def sendProtoOADealListReq(clientMsgId=None):
        request = ProtoOACashFlowHistoryListReq()
        request.ctidTraderAccountId = currentAccountId
        request.fromTimestamp = 1727740800
        request.toTimestamp = 1730908799
        deferred = client.send(
            request,
            clientMsgId=clientMsgId,
        )
        deferred.addErrback(onError)

    commands = {
        "ProtoOADealListReq": sendProtoOADealListReq,
    }

    def executeUserCommand():
        try:
            print("\n")
            userInput = inputimeout("Command (ex help): ", timeout=18)
        except TimeoutOccurred:
            print("Command Input Timeout")
            reactor.callLater(3, callable=executeUserCommand)
            return
        userInputSplit = userInput.split(" ")
        if not userInputSplit:
            print("Command split error: ", userInput)
            reactor.callLater(3, callable=executeUserCommand)
            return
        command = userInputSplit[0]
        try:
            parameters = [
                parameter if parameter[0] != "*" else parameter[1:]
                for parameter in userInputSplit[1:]
            ]
        except:
            print("Invalid parameters: ", userInput)
            reactor.callLater(3, callable=executeUserCommand)
        if command in commands:
            commands[command](*parameters)
        else:
            print("Invalid Command: ", userInput)
            reactor.callLater(3, callable=executeUserCommand)

    # Setting optional client callbacks
    client.setConnectedCallback(connected)
    client.setDisconnectedCallback(disconnected)
    client.setMessageReceivedCallback(onMessageReceived)
    # Starting the client service
    client.startService()
    reactor.run()
