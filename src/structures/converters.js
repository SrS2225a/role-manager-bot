function ConvertDate(time) {
    if (time == null) {
        return undefined;
    } else {
        let date = Date.parse(time) / 1000
        if (!date) {
            const times = time.match(/\d+\s*\w+/g);
            let years = 0;
            let months = 0;
            let weeks = 0;
            let days = 0;
            let hours = 0;
            let minutes = 0;
            let seconds = 0;
            if (times) {
                times.forEach(time => {
                    const value = time.match(/\d+/g)[0];
                    const label = time.match(/(?<=\s|\d)(mo|[ywdhms])/gi)[0];

                    switch (label) {
                        case 'y':
                            years = value * 365 * 24 * 60 * 60;
                            break;

                        case 'mo':
                            months = value * 30 * 24 * 60 * 60;
                            break;

                        case 'w':
                            weeks = value * 7 * 24 * 60 * 60;
                            break;

                        case 'd':
                            days = value * 24 * 60 * 60;
                            break;

                        case 'h':
                            hours = value * 60 * 60;
                            break;

                        case 'm':
                            minutes = value * 60;
                            break;

                        case 's':
                            seconds = value;
                            break;
                    }
                });
                return years + months + weeks + days + hours + minutes + seconds
            } else {
                return undefined
            }
        } else {
            return date.time
        }
    }
}

function display_time(duration, display_to=7) {
    const intervals = [['years', 31556952], ['months', 2592000], ['weeks', 604800], ['days', 86400], ['hours', 3600], ['minutes', 60], ['seconds', 1]]
    const result = []
    for(let x = 0; x < display_to; x++) {
        const value = Math.floor(duration / intervals[x][1])
        if(value) {
            duration -= value * intervals[x][1]
            result.push(Math.round(value) + ' ' + intervals[x][0])
        }
    }
    return result.join(', ') || `0 ${intervals[display_to-1][0]}`
}

function ProgressBar(total, current, ncols=20, char=['■', '□']) {
    const current_progress = current / total
    const filled_bar_length = (current_progress * ncols).toFixed(0)
    const empty_bar_length = ncols - filled_bar_length
    let filled_bar = get_bar(filled_bar_length, char[0])
    let empty_bar = get_bar(empty_bar_length, char[1])
    let percentage_progress = (current_progress * 100).toFixed(2)
    return `${percentage_progress}% | ${filled_bar}${empty_bar}`

    function get_bar(length, char) {
        let str = ""
        for (let i = 0; i < length; i++) {
           str += char
        }
        return str
    }
}

module.exports = {ConvertDate, display_time, ProgressBar}