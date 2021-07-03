<div class='post-list-header'><%
    %><form class='horizontal search'><%
        %><%= ctx.makeTextInput({text: 'Search query', id: 'search-text', name: 'search-text', placeholder: 'search for stuff here!', value: ctx.parameters.query}) %><%
        %><wbr/><%
        %><input class='mousetrap' type='submit' value='Search'/><%
        %><wbr/><%
        %><% if (ctx.enableSafety) { %><%
            %><input data-safety=safe title="Safe For Work content. Family friendly!" type='button' class='mousetrap safety safety-safe <%- ctx.settings.listPosts.safe ? '' : 'disabled' %>'>Safe</input><%
            %><input data-safety=sketchy title="Potentially unsafe content. You might want to be careful!" type='button' class='mousetrap safety safety-sketchy <%- ctx.settings.listPosts.sketchy ? '' : 'disabled' %>'>Sketchy</input><%
            %><input data-safety=unsafe title="Not Safe For Work content. Definitely don't browse these at work!" type='button' class='mousetrap safety safety-unsafe <%- ctx.settings.listPosts.unsafe ? '' : 'disabled' %>'>NSFW</input><%
        %><% } %><%
        %><wbr/><%
        %><a class='mousetrap button append' href='<%- ctx.formatClientLink('help', 'search', 'posts') %>'>Syntax help</a><%
    %></form><%
    %><% if (ctx.canBulkEditTags) { %><%
        %><form class='horizontal bulk-edit bulk-edit-tags'><%
            %><span class='append hint'>Tagging with:</span><%
            %><a href class='mousetrap button append open'>Mass tag</a><%
            %><wbr/><%
            %><%= ctx.makeTextInput({name: 'tag', value: ctx.parameters.tag}) %><%
            %><input class='mousetrap start' type='submit' value='Start tagging'/><%
            %><a href class='mousetrap button append close'>Stop tagging</a><%
        %></form><%
    %><% } %><%
    %><% if (ctx.enableSafety && ctx.canBulkEditSafety) { %><%
        %><form class='horizontal bulk-edit bulk-edit-safety'><%
            %><a href class='mousetrap button append open'>Mass edit safety</a><%
            %><a href class='mousetrap button append close'>Stop editing safety</a><%
        %></form><%
    %><% } %><%
%></div>
