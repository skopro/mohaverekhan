function get(url, success_function) {
    return $.ajax({
        url: url,
        type: "GET",
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function(result, status, xhr)
        {
            console.log(xhr)
            success_function(result,status,xhr)
        },
        error: function(xhr, status, error)
        {
            $("#output-text").text(`error : ${status} - ${error}`);
            alert(`error : ${status} - ${error}`)
        },
        timeout: 120 * 1000
    })
}

function post(url, data, success_function) {
    return $.ajax({
        url: url,
        type: "POST",
        data: data,
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function(result, status, xhr)
        {
            console.log(xhr)
            success_function(result,status,xhr)
        },
        error: function(xhr, status, error)
        {
            $("#output-text").text(`error : ${status} - ${error}`);
            alert(`error : ${status} - ${error}`)
        },
        timeout: 120 * 1000
    })
}

base_api_url = `http://127.0.0.1:8000/mohaverekhan/api`
normalizers_url = `${base_api_url}/normalizers`
texts_url = `${base_api_url}/texts`
normal_texts_url = `${base_api_url}/normal_texts`
tags_url = `${base_api_url}/tags`
tag_sets_url = `${base_api_url}/tag_sets`
taggers_url = `${base_api_url}/taggers`
sentences_url = `${base_api_url}/sentences`
tagged_sentences_url = `${base_api_url}/tagged_sentences`
translation_characters_url = `${base_api_url}/rules/translation_characters`
refinement_patterns_url = `${base_api_url}/rules/refinement_patterns`

selected_normalizer = "no-normalizer"
selected_tagger = "no-tagger"
text_id = "no-id"
input_text = "no-text"
output_text = "no-text"

function do_after_success_getting_taggers(result, status, xhr) {
    for ( var i in xhr.responseJSON) {
        tagger = xhr.responseJSON[i]
        console.log(tagger.name)
        console.log(tagger.model_type)
        if (tagger.model_type == "manual")
            continue
        // $( "#taggers" ).append( `"<option>${tagger.name}</option>"` );
        $( "#taggers" ).append($("<option></option>")
                .attr("value", tagger.name)
                .text(tagger.name)); 
    }
    $('.selectpicker').selectpicker('refresh');
}

function do_after_success_getting_normalizers(result, status, xhr) {
    for ( var i in xhr.responseJSON) {
        normalizer = xhr.responseJSON[i]
        console.log(normalizer.name)
        console.log(normalizer.model_type)
        if (normalizer.model_type == "manual")
            continue
        // $( "#normalizers" ).append( `"<option>${normalizer.name}</option>"` );
        $( "#normalizers" ).append($("<option></option>")
                .attr("value", normalizer.name)
                .text(normalizer.name)); 
    }
    $('.selectpicker').selectpicker('refresh');
}

get(`${taggers_url}`, do_after_success_getting_taggers)
get(`${normalizers_url}`, do_after_success_getting_normalizers)

$(document).ready(function(){

    var csrftoken = Cookies.get('csrftoken');
    function csrfSafeMethod(method) {
        // these HTTPs methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
                // xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    function do_after_success_tagging_text(result, status, xhr) {
        html = ''
        for (var i in xhr.responseJSON.sentences) {
            sentence = xhr.responseJSON.sentences[i]
            console.log(`sentence : ${sentence.content}`)
            for (var j in sentence.tagged_sentences) {
                tagged_sentence = sentence.tagged_sentences[j]
                if (tagged_sentence.tagger != selected_tagger)
                    continue
                for (var k in tagged_sentence.tokens) {
                    token = tagged_sentence.tokens[k]
                    console.log(`token : ${token}`)
                    html += `<div style="color:${token.tag.color};display: inline-block;">${token.content}_${token.tag.name}&nbsp;&nbsp;&nbsp;</div>`
                    console.log(html)
                }
                html +=`<br />`
            }
        }
        console.log(html)
        $("#output-text").html(html);
    }
    function do_after_success_normalizing_text(result, status, xhr) {
        text_id = xhr.responseJSON.id
        console.log(`text_id (normal) : ${text_id}`)
        if (selected_tagger != "no-tagger") {
            get(`${taggers_url}/${selected_tagger}/tag?text-id=${text_id}`, do_after_success_tagging_text)
        }
        else {
            // $("#output-text").html(xhr.responseJSON.content)
            $("#output-text").html(xhr.responseJSON.content.replace(/\n/g, "<br>"))
        }
    }
    function do_after_success_getting_item(result, status, xhr) {
        var text = xhr.responseJSON
        text_id = text.id
        console.log(`text_id : ${text_id}`)
        console.log(`text content : ${text}`)
        if (selected_normalizer != "no-normalizer") {
            get(`${normalizers_url}/${selected_normalizer}/normalize?text-id=${text_id}`, do_after_success_normalizing_text)
        }
        else if (selected_tagger != "no-tagger") {
            get(`${taggers_url}/${selected_tagger}/tag?text-id=${text_id}`, do_after_success_tagging_text)
        }
    }

    $("#do-it-button").click(function() {
        input_text = $("#input-text").val()
        console.log(`input_text : ${input_text}`)

        selected_normalizer = $("#normalizers").children("option:selected").val();
        console.log(`selected_normalizer : ${selected_normalizer}`)

        selected_tagger = $("#taggers").children("option:selected").val();
        console.log(`selected_tagger : ${selected_tagger}`)

        if ( selected_normalizer == "no-normalizer" && selected_tagger == "no-tagger") {
            $("#output-text").text('لطفا حداقل یک رسمی کننده یا یک برچسب زننده انتخاب کنید.');
            return
        }

        input_text = input_text.replace(/\n/g, "\\n")
        console.log(`input_text : \n${input_text}\n`)

        var data = `{"content": "${input_text}"}`
        console.log(`data : ${data}`)

        post(texts_url, data, do_after_success_getting_item)

        // input_text = $('#input-text').clone().children().remove().end().text() + '\n';
        // current_line = ''
        // $("#input-text").children('div').each(function () {
        //     current_line = $(this).text()
        //     if (current_line != '')
        //         input_text += current_line + '\n';
        // });
        // console.log(`input_text : ${input_text}`)

        
    })
    

    

        // $.when( post(texts_url, data) ).then(function( data, textStatus, jqXHR ) {
        //     $.when( post(tag_text, data) ).then(function( data, textStatus, jqXHR ) {
        //         alert( jqXHR.status ); // Alerts 200
        //       });
        //   });

});

