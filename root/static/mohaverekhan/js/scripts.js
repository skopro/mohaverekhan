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

  $("#change-to-formal-button").click(function(){
    var input_text = $("#input-text").text();
    
    var url = 'http://127.0.0.1:8000/ippost/api/texts/convert_to_formal/'
    var data = `{"content": "${input_text}"}`
    console.log(`POST ${url}\n\n\n${data}`)
    $.ajax({
      url: url,
      type: "POST",
      data: data,
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function(result, status, xhr)
      {
        // var results = $.map(data, function(item)
        // {
        //   return { value: item.value, id: item.id }
        // }); 
        $("#output-text").text(result.formal_content);
      },
      error: function(xhr, status, error){
        
        $("#output-text").text(`error : ${status} - ${error}`);
        alert(`error : ${status} - ${error}`)
      },
      timeout: 120 * 1000
    })

  })

  $("#convert_and_fpost-button").click(function(){
    var input_text = $("#input-text").text();
    
    var url = 'http://127.0.0.1:8000/ippost/api/texts/convert_and_fpost/'
    var data = `{"content": "${input_text}"}`
    console.log(`POST ${url}\n\n\n${data}`)
    $.ajax({
      url: url,
      type: "POST",
      data: data,
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function(result, status, xhr)
      {
        // var results = $.map(data, function(item)
        // {
        //   return { value: item.value, id: item.id }
        // }); 
        // $("#output-text").text(result.fpost_content);
        $("#output-text").text(result);
      },
      error: function(xhr, status, error){
        
        $("#output-text").text(`error : ${status} - ${error}`);
        alert(`error : ${status} - ${error}`)
      },
      timeout: 120 * 1000
    })

  })

  $("#infpost-button").click(function(){
    var input_text = $("#input-text").text();
    var url = 'http://127.0.0.1:8000/ippost/api/texts/infpost/'
    var data = `{"content": "${input_text}"}`
    console.log(`POST ${url}\n\n\n${data}`)
    $.ajax({
      url: url,
      type: "POST",
      data: data,
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function(result, status, xhr)
      {
        // var results = $.map(data, function(item)
        // {
        //   return { value: item.value, id: item.id }
        // }); 
        // $("#output-text").text(xhr.responseText);
        // console.log(`result : ${result}`)
        // console.log(`status : ${status}`)
        // console.log(`xhr : ${xhr}`)
        // console.log(`xhr.responseJSON : ${xhr.responseJSON}`)
        // console.log(`xhr.responseText : ${xhr.responseText}`)
        // console.log(`result : ${result}`)
        console.log(result)
        console.log(status)
        console.log(xhr)
        console.log(xhr.responseJSON)
        console.log(xhr.responseText)
        html = ''
        // var parsed_data = JSON.parse(xhr.responseText);
        // console.log(`parsed_data : ${parsed_data}`)
        for (var i in xhr.responseJSON.sentences) {
            sentence = xhr.responseJSON.sentences[i]
        // for (var sentence in parsed_data) {
            console.log(`sentence : ${sentence}`)
            for (var j in sentence.tokens) {
                token = sentence.tokens[j]
                console.log(`token : ${token}`)
                html += `<div style="color:${token.tag.color};display: inline-block;">${token.content}_${token.tag.name}&nbsp;&nbsp;&nbsp;</div>`
                console.log(html)
            }
            html +=`<br />`
        }
        // var text = ''
        // for (var key in result) {
        //     if (result.hasOwnProperty(key)) {
        //         text += ` ${key} -> ${result[key]}\n`
        //     }
            
        // }
        // $("#output-text").html("<p>Status:" + status + "</p>\n" + "<p>Data:</p>" + "<pre>" + result + "</pre>");
        console.log(html)
        $("#output-text").html(html);
        console.log(result)
        // $("#output-text").text(result.infpost_content);
      },
      error: function(xhr, status, error){
        
        $("#output-text").text(`error : ${status} - ${error}`);
        alert(`error : ${status} - ${error}`)
      },
      timeout: 120 * 1000
    })

  })

});
// function change_to_formal() {
  
//   const input_text = document.getElementById('input-text');
//   const output_text = document.getElementById('output-text');
//   console.log(`input_text : ${input_text}`);
//   console.log(`input_text.innerHTML : ${input_text.innerHTML}`);
//   console.log(`input_text.innerText : ${input_text.innerText}`);
//   console.log(`output_text : ${output_text}`);

//   var xhr = new XMLHttpRequest();
//   // Open a new connection, using the GET request on the URL endpoint
//   xhr.open('Post', 'http://127.0.0.1:8000/ippost/texts/convert_to_formal/', true);
//   xhr.setRequestHeader("Content-Type", "application/json");
//   xhr.onload = function () {
//       var data = JSON.parse(this.response);

//       if (xhr.status >= 200 && xhr.status < 400) {
//           output_text.textContent = data.formal_content;
//           // data.forEach(word => {
//           //     output_text.textContent += '{0} => {1}\r\n'.format(word.informal, word.formal)
//           // });
//         } else {
//           output_text.textContent = `خطایی بوجود آمده است\n${xhr.status} : ${xhr.statusText}`
//           console.log('error');
//         }
//       xhr.abort();
//   }

//   // Send request
//   var input_json = `{"content": "${input_text.innerText}"}`;
//   console.log(`input_json : ${input_json}`);
//   xhr.send(input_json);
// }

// document.getElementById('change-to-formal-button').onclick = change_to_formal;

