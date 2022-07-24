if (!window.dash_clientside) {
    window.dash_clientside = {};
}
window.minty_colors = ['#78c2ad', '#f3969a', '#6cc3d5', '#ffce67', '#ff7851']
window.drake = dragula();
window.dash_clientside.clientside = {
    make_draggable: function() {
        let args = Array.from(arguments)[0];
        var els = [];
        window.drake.destroy();
        setTimeout(function() {
            for (i = 0; i < args.length; i++){
                els[i] = document.getElementById(JSON.stringify(args[i]));
            }
            window.drake = dragula(els);
        }, 1)
        return window.dash_clientside.no_update
    },

    update_student_card: function(data) {
        if(!data) {
            return ['', '', '', '', '', '', '', '', '', ''];
        }
        // TODO incorporate the no_update exception,
        // so components that did not change, don't update
        // should lead to better performance, so we don't
        // initiate callbacks down the chain if we don't need to
        return [
            `${data.card_info} shadow-card`,
            `${data.sentences} sentences`,
            `${data.paragraphs} paragraphs`,
            `${data.time_on_task} minutes on task`,
            `${data.unique_words} unique words`,
            data.text,
            data.transition_words,
            data.use_of_synonyms,
            data.sv_agreement,
            data.formal_language,
        ];
    },

    populate_student_data: function(msg, old_data, students) {
        if (!msg) {
            return []
        }
        let updates = Array(students).fill(window.dash_clientside.no_update);
        const data = JSON.parse(msg.data);
        for (const up of data) {
            let index = up.id
            updates[index] = {...old_data[index], ...up};
        }
        return updates;
    },

    update_student_progress_bars: function(value) {
        const options = ['secondary', 'warning', 'primary'];
        return options[value%3-1];
    },

    update_analysis_data: function(msg) {
        if(!msg){
            return {
                data: [{y: [], type: "scatter"}]
            };
        }
        const data = JSON.parse(msg.data);
        return {
            data: [{
                y: data.data,
                type: data.id,
                marker: {
                    color: window.minty_colors[0]
                }
            }],
            layout: {
                title: data.id,
            }
        };
    },

    open_offcanvas: function(clicks, is_open) {
        if(clicks) {
            return !is_open
        }
        return is_open
    },

    toggle_progress_checklist: function(values) {
        if (values.includes('progress')) {
            return true;
        }
        return false;
    },

    hide_show_attributes: function(values, progress, students) {
        let sentence_badge = 'd-none';
        let paragraph_badge = 'd-none';
        let time_on_task_badge = 'd-none';
        let unique_words_badge = 'd-none';
        let text_area = 'd-none';
        let progress_div = 'd-none';
        let transition_words = 'd-none';
        let use_of_synonyms = 'd-none';
        let sv_agreement = 'd-none';
        let formal_language = 'd-none';
        if (values.includes('sentences')) {
            sentence_badge = 'mb-1';
        }
        if (values.includes('paragraphs')) {
            paragraph_badge = 'mb-1';
        }
        if (values.includes('time_on_task')) {
            time_on_task_badge = 'mb-1';
        }
        if (values.includes('unique_words')) {
            unique_words_badge = 'mb-1';
        }
        if (values.includes('text')) {
            text_area = '';
        }
        if (values.includes('progress')) {
            // TODO there is probably a better way to do this
            // in more algorithmic way
            // requires a deeper discussion on what is shown
            progress_div = ''
            if (progress.includes('transition_words')) {
                transition_words = ''
            }
            if (progress.includes('use_of_synonyms')) {
                use_of_synonyms = ''
            }
            if (progress.includes('sv_agreement')) {
                sv_agreement = ''
            }
            if (progress.includes('formal_language')) {
                formal_language = ''
            }
        }
        return [
            Array(students).fill(sentence_badge),
            Array(students).fill(paragraph_badge),
            Array(students).fill(time_on_task_badge),
            Array(students).fill(unique_words_badge),
            Array(students).fill(text_area),
            Array(students).fill(progress_div),
            Array(students).fill(transition_words),
            Array(students).fill(use_of_synonyms),
            Array(students).fill(sv_agreement),
            Array(students).fill(formal_language),
        ]
    }
}
