#!/usr/bin/python3
from operator import truediv
import os, sys, time, json

from regex import P


## This is the definition for a tiny lambda function
## Which is run in response to messages processed in Doover's 'Channels' system

## In the doover_config.json file we have defined some of these subscriptions
## These are under 'processor_deployments' > 'tasks'


## You can import the pydoover module to interact with Doover based on decisions made in this function
## Just add the current directory to the path first
sys.path.append(os.path.dirname(__file__))
import pydoover as pd


class target:

    def __init__(self, *args, **kwargs):

        self.kwargs = kwargs
        ### kwarg
        #     'agent_id' : The Doover agent id invoking the task e.g. '9843b273-6580-4520-bdb0-0afb7bfec049'
        #     'access_token' : A temporary token that can be used to interact with the Doover API .e.g 'ABCDEFGHJKLMNOPQRSTUVWXYZ123456890',
        #     'api_endpoint' : The API endpoint to interact with e.g. "https://my.doover.com",
        #     'package_config' : A dictionary object with configuration for the task - as stored in the task channel in Doover,
        #     'msg_obj' : A dictionary object of the msg that has invoked this task,
        #     'task_id' : The identifier string of the task channel used to run this processor,
        #     'log_channel' : The identifier string of the channel to publish any logs to


    ## This function is invoked after the singleton instance is created
    def execute(self):

        start_time = time.time()

        self.create_doover_client()

        self.add_to_log( "kwargs = " + str(self.kwargs) )
        self.add_to_log( str( start_time ) )

        try:
            
            ## Do any processing you would like to do here
            message_type = None
            if 'message_type' in self.kwargs['package_config'] and 'message_type' is not None:
                message_type = self.kwargs['package_config']['message_type']

            if message_type == "DEPLOY":
                self.deploy()

            if message_type == "DOWNLINK":
                self.downlink()

            if message_type == "UPLINK":
                self.uplink()

        except Exception as e:
            self.add_to_log("ERROR attempting to process message - " + str(e))

        self.complete_log()



    def deploy(self):
        ## Run any deployment code here
        
        ## Get the deployment channel
        ui_state_channel = self.cli.get_channel(
            channel_name="ui_state",
            agent_id=self.kwargs['agent_id'] )

        ui_obj = {
            "state" : {
                "type" : "uiContainer",
                "displayString" : "",
                "children" : {
                    "isWorking" : {
                        "type" : "uiVariable",
                        "varType" : "float",
                        "name" : "isWorking",
                        "displayString" : "Is it Working?",
                        "currentValue" : True
                    }
                }
            }
        }

        ui_state_channel.publish(
            msg_str=json.dumps(ui_obj)
        )


    def downlink(self):
        ## Run any downlink processing code here
        pass

    def uplink(self):
        ## Run any uplink processing code here
        pass


    def create_doover_client(self):
        self.cli = pd.doover_iface(
            agent_id=self.kwargs['agent_id'],
            access_token=self.kwargs['access_token'],
            endpoint=self.kwargs['api_endpoint'],
        )

    def add_to_log(self, msg):
        if not hasattr(self, '_log'):
            self._log = ""
        self._log = self._log + str(msg) + "\n"

    def complete_log(self):
        if hasattr(self, '_log') and self.log is not None:
            log_channel = self.cli.get_channel( channel_id=self.kwargs['log_channel'] )
            log_channel.publish(
                msg_str=self._log
            )