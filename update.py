from classes.episode import Episode
from classes.channel import Channel
from classes.guest import Guest

from setup import read_channel, insert_channel, get_channel_details, get_video_ids, insert_video, update_video, read_video, get_episodes

def update_db():
    """
    Initialise the database and create the tables if needed.
    Check the channel details for updates.
    Get the video ids from the channel id.
    Get the episode details from the video ids.
    Update the database with the episode details if needed.
    """
    # set channel id
    channelid = 'UCYCGsNTvYxfkPkfQopRMP7w'

    # try to get channel details from database
    # if there is no record, query youtube API and create a Channel object
    # if there is a record, create a Channel object from the record
    # get the channel details from the database
    channel_details = read_channel(channelid)
    if channel_details is not None:
        channel_details = Channel(channel_details[0], channel_details[1], channel_details[2], channel_details[3], channel_details[4], channel_details[5], channel_details[6], channel_details[7], channel_details[8]).to_dict()
        channel_details = get_channel_details(channelid)
    else:
        channel_details = get_channel_details(channelid)
        insert_channel(channel_details)

    # Get the video ids from the channel id
    video_ids = get_video_ids(channelid)

    # print the number of videos found
    print(str(len(video_ids)) + ' videos found')
    
    # Get the episode details from the video ids
    episode_details = get_episodes(video_ids)

    # print the number of episodes found
    print(str(len(episode_details)) + ' episodes found')

    for e in episode_details:
        ep = Episode(e['id'], e['title'], e['url'], e['description'], e['thumb'], e['published_date'], e['duration'], e['number'])
        row = read_video(e['id'])
        if row is None:
            insert_video(e)
        else:
            dbep = Episode(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
            if ep.title != dbep.title or ep.url != dbep.url or ep.description != dbep.description:
                update_video(e)

