#!/bin/bash
jq -R -s -c '{ list:split("\n")}'
